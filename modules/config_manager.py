from typing import Dict, Any, Optional
from modules.database import DatabaseConnection
from modules.sensor_registry import SensorRegistry


class ConfigManager:
    
    CONFIG_ID = "sensor_thresholds"
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self._cached_config = None
    
    def get_sensor_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        if self._cached_config is not None and not force_refresh:
            return self._cached_config
        
        config = self.db.get_config(self.CONFIG_ID)
        
        # Si no existe o no tiene sensores, cargar defaults completos
        if config is None or not config.get("sensors"):
            # Cargar TODOS los defaults conocidos (pH, Temp, DO, etc.)
            SensorRegistry._ensure_loaded()
            default_sensors = {k: v.to_dict() for k, v in SensorRegistry._defaults.items()}
            
            initial = {
                "_id": self.CONFIG_ID,
                "sensors": default_sensors
            }
            self.db.save_config(self.CONFIG_ID, initial)
            config = initial
        
        self._cached_config = config
        return config
    
    def _create_initial_config(self) -> Dict[str, Any]:
        initial_config = {
            "_id": self.CONFIG_ID,
            "sensors": {}
        }
        
        self.db.save_config(self.CONFIG_ID, initial_config)
        
        return initial_config
    
    def get_threshold_for_sensor(self, sensor_name: str) -> Optional[Dict[str, Any]]:
        config = self.get_sensor_config()
        sensors = config.get("sensors", {})
        
        return sensors.get(sensor_name)
    
    def update_sensor_threshold(self, sensor_name: str, threshold_data: Dict[str, Any]) -> bool:
        if not SensorRegistry.validate_sensor_config(threshold_data):
            raise ValueError(f"Configuración inválida para sensor {sensor_name}")
        
        config = self.get_sensor_config(force_refresh=True)
        
        if "sensors" not in config:
            config["sensors"] = {}
        
        config["sensors"][sensor_name] = threshold_data
        
        success = self.db.save_config(self.CONFIG_ID, config)
        
        if success:
            self._cached_config = None
        
        return success
    
    def update_multiple_thresholds(self, thresholds: Dict[str, Dict[str, Any]]) -> bool:
        for sensor_name, threshold_data in thresholds.items():
            if not SensorRegistry.validate_sensor_config(threshold_data):
                raise ValueError(f"Configuración inválida para sensor {sensor_name}")
        
        config = self.get_sensor_config(force_refresh=True)
        
        if "sensors" not in config:
            config["sensors"] = {}
        
        config["sensors"].update(thresholds)
        
        success = self.db.save_config(self.CONFIG_ID, config)
        
        if success:
            self._cached_config = None
        
        return success
    
    def delete_sensor_threshold(self, sensor_name: str) -> bool:
        config = self.get_sensor_config(force_refresh=True)
        
        if "sensors" not in config or sensor_name not in config["sensors"]:
            return False
        
        del config["sensors"][sensor_name]
        
        success = self.db.save_config(self.CONFIG_ID, config)
        
        if success:
            self._cached_config = None
        
        return success
    
    def reset_to_defaults(self, detected_sensors: set) -> bool:
        default_config = SensorRegistry.create_default_config(detected_sensors)
        
        config = {
            "_id": self.CONFIG_ID,
            "sensors": default_config
        }
        
        success = self.db.save_config(self.CONFIG_ID, config)
        
        if success:
            self._cached_config = None
        
        return success
    
    def sync_with_detected_sensors(self, detected_sensors: set) -> bool:
        config = self.get_sensor_config(force_refresh=True)
        
        updated_config = SensorRegistry.merge_configs(config, detected_sensors)
        
        success = self.db.save_config(self.CONFIG_ID, updated_config)
        
        if success:
            self._cached_config = None
        
        return success
    
    def get_all_configured_sensors(self) -> Dict[str, Dict[str, Any]]:
        config = self.get_sensor_config()
        return config.get("sensors", {})
    
    DEVICES_CONFIG_ID = "device_metadata"

    def get_device_metadata(self) -> Dict[str, Dict[str, str]]:
        """Recupera los metadatos de dispositivos (alias, ubicación)."""
        all_devices = self.db.get_all_devices_metadata()
        
        # Mapear nombre->alias y ubicacion->location para compatibilidad con código existente
        result = {}
        for dev_id, dev_data in all_devices.items():
            result[dev_id] = {
                "alias": dev_data.get("nombre", dev_id),  # nombre es el campo real
                "location": dev_data.get("ubicacion", "Desconocido")  # ubicacion es el campo real
            }
        return result

    def update_device_metadata(self, device_id: str, alias: str, location: str) -> bool:
        """Actualiza el nombre y ubicación de un dispositivo específico."""
        # Usar $set para actualizar solo nombre y ubicacion, preservando todo lo demás
        update_data = {
            "nombre": alias,  # El parámetro se llama 'alias' por compatibilidad, pero guardamos en 'nombre'
            "ubicacion": location  # Guardamos en 'ubicacion' (español)
        }
        
        return self.db.update_device_fields(device_id, update_data)

    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """Obtiene la info enriquecida de un dispositivo (o devuelve defaults)."""
        meta = self.get_device_metadata()
        return meta.get(device_id, {"alias": device_id, "location": "Desconocido"})
        
    def get_device_thresholds(self, device_id: str) -> Dict[str, Any]:
        """Obtiene umbrales específicos de un dispositivo (si existen)."""
        dev_data = self.db.get_device_metadata(device_id)
        if not dev_data:
            return {}
        return dev_data.get("umbrales", {})  # Usar 'umbrales' en español

    def update_device_threshold(self, device_id: str, sensor_name: str, threshold_data: Dict[str, Any]) -> bool:
        """Guarda umbrales específicos para un sensor de un dispositivo."""
        # Usar $set con dot notation para actualizar solo el threshold específico
        update_data = {
            f"umbrales.{sensor_name}": threshold_data
        }
        
        return self.db.update_device_fields(device_id, update_data)