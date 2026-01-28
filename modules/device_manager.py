import pandas as pd
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# --- ENUMS ---
class ConnectionStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"

class HealthStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

# --- DTO ---
@dataclass
class DeviceInfo:
    device_id: str
    location: str
    last_update: Optional[datetime]
    connection: ConnectionStatus
    health: HealthStatus
    sensor_data: Dict[str, float] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)

# --- CLASE PRINCIPAL ---
class DeviceManager:
    
    OFFLINE_TIMEOUT_SECONDS = 60 # Tiempo de tolerancia para Offline
    
    def __init__(self, global_thresholds: Dict[str, Any], previous_health: Dict[str, HealthStatus] = None, device_specific_thresholds: Dict[str, Dict[str, Any]] = None):
        """
        global_thresholds: Configuración base para todos los sensores.
        device_specific_thresholds: {device_id: {sensor_name: config}}
        """
        self.global_thresholds = global_thresholds
        self.device_specific_thresholds = device_specific_thresholds or {}
        self._previous_health: Dict[str, HealthStatus] = previous_health or {}
    
    def get_health_states(self) -> Dict[str, HealthStatus]:
        return self._previous_health

    def get_all_devices_info(self, df: pd.DataFrame) -> List[DeviceInfo]:
        if df is None or df.empty:
            return []
        records = df.to_dict('records')
        return [self._process_single_record(row) for row in records]
    
    def _process_single_record(self, row: Dict) -> DeviceInfo:
        device_id = str(row.get("device_id", "Unknown"))
        location = str(row.get("location", "Sin ubicacion"))
        
        # Parse Timestamp
        ts = row.get("timestamp")
        timestamp = None
        if not pd.isna(ts) and ts is not pd.NaT:
            if isinstance(ts, pd.Timestamp): timestamp = ts.to_pydatetime()
            else: timestamp = ts

        # Parse Sensors
        sensor_values = self._extract_sensor_values(row.get("sensor_data", row.get("sensors", {})))
        
        # Parse Alerts
        raw_alerts = row.get("alerts")
        alerts = []
        if isinstance(raw_alerts, list): alerts = [str(a) for a in raw_alerts]
        elif isinstance(raw_alerts, str): alerts = [raw_alerts]
        
        # Evaluacion
        connection = self._evaluate_connection(timestamp)
        
        if connection == ConnectionStatus.ONLINE:
            health = self._evaluate_health(device_id, sensor_values, alerts)
        else:
            health = HealthStatus.UNKNOWN # O mantener previous si queremos "memoria"
            # Para dashboard en tiempo real, si esta offline, el health es irrelevante o unknown
        
        return DeviceInfo(
            device_id=device_id,
            location=location,
            last_update=timestamp,
            connection=connection,
            health=health,
            sensor_data=sensor_values,
            alerts=alerts
        )
    
    def _extract_sensor_values(self, raw: Any) -> Dict[str, float]:
        values = {}
        if not isinstance(raw, dict): return values
        
        for k, v in raw.items():
            val = None
            if isinstance(v, dict) and 'value' in v: val = v['value']
            else: val = v
            
            if isinstance(val, (int, float)) and not pd.isna(val):
                values[k] = float(val)
        return values

    def _evaluate_connection(self, timestamp: Optional[datetime]) -> ConnectionStatus:
        if timestamp is None: return ConnectionStatus.OFFLINE
        
        # Zona horaria de Chile (UTC-3)
        chile_tz = timezone(timedelta(hours=-3))
        
        # Obtener hora actual en Chile (naive para comparar con timestamp normalizado)
        now_chile = datetime.now(chile_tz).replace(tzinfo=None)
        ts_clean = timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp
        
        diff_seconds = abs((now_chile - ts_clean).total_seconds())
        
        if diff_seconds > self.OFFLINE_TIMEOUT_SECONDS:
            return ConnectionStatus.OFFLINE
        return ConnectionStatus.ONLINE

    def _evaluate_health(self, device_id: str, sensors: Dict[str, float], alerts: List[str]) -> HealthStatus:
        # 1. Alertas explicitas del dispositivo
        if alerts:
            self._previous_health[device_id] = HealthStatus.CRITICAL
            return HealthStatus.CRITICAL
            
        new_health = HealthStatus.OK
        
        # Obtener Thresholds Específicos de este dispositivo
        dev_thresholds = self.device_specific_thresholds.get(device_id, {})
        
        for sensor, value in sensors.items():
            # Buscar config: Específica > Global
            config = dev_thresholds.get(sensor, self.global_thresholds.get(sensor))
            
            if not config: continue
            
            # Interpretar Configuración de Umbrales
            
            # Mapping robusto: Soporta nomenclatura nueva (JSON) y antigua
            # JSON: min (Rojo), optimal_min (Verde Start), optimal_max (Verde End), max (Rojo)
            
            c_min = float(config.get("min", config.get("critical_min", -9999)))
            c_max = float(config.get("max", config.get("critical_max", 9999)))
            o_min = float(config.get("optimal_min", config.get("min_value", -9999))) 
            o_max = float(config.get("optimal_max", config.get("max_value", 9999)))
            
            # Evaluación
            state = HealthStatus.OK
            
            # Critico
            if value < c_min or value > c_max:
                state = HealthStatus.CRITICAL
            # Warning (Zona entre Crítico y Óptimo)
            elif value < o_min or value > o_max:
                state = HealthStatus.WARNING
            
            # Prioridad de Estados: Critical > Warning > OK
            if state == HealthStatus.CRITICAL:
                new_health = HealthStatus.CRITICAL
                break # Ya es crítico, no puede empeorar
            elif state == HealthStatus.WARNING and new_health != HealthStatus.CRITICAL:
                new_health = HealthStatus.WARNING
        
        self._previous_health[device_id] = new_health
        return new_health

    def calculate_summary_metrics(self, devices: List[DeviceInfo]) -> Dict[str, int]:
        return {
            "total": len(devices),
            "online": sum(1 for d in devices if d.connection == ConnectionStatus.ONLINE),
            "offline": sum(1 for d in devices if d.connection == ConnectionStatus.OFFLINE),
            "ok": sum(1 for d in devices if d.health == HealthStatus.OK),
            "warning": sum(1 for d in devices if d.health == HealthStatus.WARNING),
            "critical": sum(1 for d in devices if d.health == HealthStatus.CRITICAL),
        }