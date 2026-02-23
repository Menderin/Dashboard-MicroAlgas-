import os
import time
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import certifi
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

# Cargar variables de entorno
load_dotenv()

# --- PATRÓN SINGLETON (CONEXIÓN ROBUSTA) ---
@st.cache_resource(ttl=3600, show_spinner=False)
def get_mongo_client(uri: str) -> Optional[MongoClient]:
    if not uri: return None
    try:
        client = MongoClient(
            uri,
            connectTimeoutMS=30000,
            retryWrites=True,
            tls=True,
            tlsCAFile=certifi.where(),
            tz_aware=True
        )
        # Ping rapido para validar
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Error conexión MongoDB: {str(e)}")
        return None

class DatabaseConnection:
    CONFIG_COLLECTION = "system_config"

    def __init__(self):
        # 1. Configuración de Fuente Única
        self.uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB")
        self.coll_name = os.getenv("MONGO_COLLECTION", "sensors_data")
        self.client = get_mongo_client(self.uri)
        
        if not self.client:
            print("Error: No se pudo establecer conexión con MongoDB")
            
    @property
    def db(self):
        if self.client:
            return self.client[self.db_name]
        return None

    @property
    def collection(self):
        if self.db is not None:
            return self.db[self.coll_name]
        return None

    @property
    def devices_collection(self):
        """Colección dedicada para metadatos de dispositivos."""
        if self.db is not None:
            devices_coll = os.getenv("MONGO_COLLECTION_DISPOSITIVOS", "devices_data")
            return self.db[devices_coll]
        return None

    # --- MÉTODOS ADAPTER (Normalización) ---
    def _normalize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """ADAPTER: Normaliza documentos de diferentes esquemas a un formato unificado."""
        if not doc: return {}
        
        # 1. Normalizar ID de Dispositivo
        dev_id = doc.get("device_id")
        if not dev_id:
            dev_id = doc.get("dispositivo_id")
        if not dev_id:
            dev_id = doc.get("metadata", {}).get("device_id", "unknown")
            
        # 2. Normalizar Sensores
        sensors = doc.get("sensors", {})
        if not sensors:
            sensors = doc.get("datos", {})
            
        # 3. Normalizar Timestamp
        raw_ts = doc.get("timestamp")
        final_ts = None
        
        try:
            if isinstance(raw_ts, dict) and "$date" in raw_ts:
                raw_ts = raw_ts["$date"]
                
            if isinstance(raw_ts, (int, float)):
                # Forzar interpretation como UTC
                if raw_ts > 1e11: 
                    final_ts = pd.to_datetime(raw_ts, unit='ms', utc=True).to_pydatetime()
                else:
                    final_ts = pd.to_datetime(raw_ts, unit='s', utc=True).to_pydatetime()
            elif isinstance(raw_ts, str):
                final_ts = pd.to_datetime(raw_ts, errors='coerce', utc=True)
                if not pd.isna(final_ts):
                     final_ts = final_ts.to_pydatetime()
                else:
                     final_ts = None
            elif isinstance(raw_ts, datetime):
                final_ts = raw_ts
                # Si pymongo nos da naive, asumimos UTC manualmente (caso raro con tz_aware=True)
                if final_ts.tzinfo is None:
                    final_ts = final_ts.replace(tzinfo=timezone.utc)
        except Exception:
            final_ts = None
        
        if final_ts is not None:
             if final_ts.tzinfo is not None:
                 # Si viene con zona horaria (UTC de Mongo), convertir a Chile (UTC-3)
                 chile_tz = timezone(timedelta(hours=-3))
                 final_ts = final_ts.astimezone(chile_tz)
                 final_ts = final_ts.replace(tzinfo=None) # Hacer naive para compatibilidad interna
        
        # Normalizar ID de config/mongo para evitar conflictos si se usa como key
        oid = str(doc.get("_id", ""))
        
        # 4. Normalizar nombres de sensores y extraer valores
        # Soporta dos formatos:
        # - Plano: {"temperature": 19.85}
        # - Anidado: {"temperature": {"value": 19.85, "unit": "C", "valid": true}}
        normalized_sensors = {}
        for key, value in sensors.items():
            norm_key = key.lower().strip()
            
            # Manejar aliases comunes
            if norm_key in ["temp", "temperatura"]:
                norm_key = "temperature"
            elif norm_key in ["oxigeno", "od", "do"]:
                norm_key = "oxygen"
            
            # Extraer el valor numérico
            final_value = None
            if isinstance(value, dict):
                # Formato anidado: {"value": 19.85, "unit": "C", ...}
                final_value = value.get("value")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                # Formato plano: 19.85
                final_value = value
            
            # Solo agregar si es un valor numérico válido
            if final_value is not None and norm_key not in normalized_sensors:
                try:
                    normalized_sensors[norm_key] = float(final_value)
                except (ValueError, TypeError):
                    pass  # Ignorar valores no convertibles
            
        return {
            "device_id": dev_id,
            "timestamp": final_ts,
            "location": doc.get("location", "Sin Asignar"),
            "sensors": normalized_sensors,
            "alerts": doc.get("alerts", []),
            "_source_id": oid 
        }

    # --- MÉTODO PARA DASHBOARD (Single-DB Optimized) ---
    def get_latest_by_device(self) -> pd.DataFrame:
        if self.collection is None: return pd.DataFrame()
        
        try:
            # AGREGACIÓN para obtener el documento más reciente de CADA dispositivo
            # Esto soluciona el problema de dispositivos inactivos que quedan fuera del limit(1000) simple
            pipeline = [
                {"$sort": {"timestamp": -1}},
                {"$group": {
                    "_id": {
                        "$ifNull": ["$device_id", "$dispositivo_id"] # Manejar ambos nombres de campo ID
                    },
                    "latest_doc": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$latest_doc"}}
            ]
            
            documents = list(self.collection.aggregate(pipeline))
            
            all_docs = []
            for raw_doc in documents:
                norm_doc = self._normalize_document(raw_doc)
                if norm_doc["device_id"] and norm_doc["device_id"] != "unknown":
                    all_docs.append(norm_doc)
                    
            return self._rows_to_dataframe(all_docs)
                        
        except Exception as e:
            print(f"Error fetching latest devices: {str(e)}")
            return pd.DataFrame()

    def get_latest_for_single_device(self, device_id: str) -> pd.DataFrame:
        """Busca el dispositivo en la fuente única."""
        if self.collection is None: return pd.DataFrame()
        
        try:
            query = {
                "$or": [
                    {"device_id": device_id},
                    {"dispositivo_id": device_id}
                ]
            }
            
            doc = self.collection.find_one(query, sort=[("timestamp", -1)])
            if doc:
                norm_doc = self._normalize_document(doc)
                return self._rows_to_dataframe([norm_doc])
                
        except Exception:
            pass
                
        return pd.DataFrame()

    # --- METODOS PARA HISTORIAL Y GRAFICOS ---
    def fetch_data(self, start_date=None, end_date=None, device_ids=None, limit=5000) -> pd.DataFrame:
        if self.collection is None: return pd.DataFrame()
        
        try:
            mongo_query = {}
            
            if device_ids:
                mongo_query["$or"] = [
                    {"device_id": {"$in": device_ids}},
                    {"dispositivo_id": {"$in": device_ids}}
                ]
            
            # Filtro de fecha en Mongo si es posible (más eficiente)
            # Nota: Requiere que start_date/end_date sean datetime y timestamp en BD sea Date o compatible
            # Por seguridad lo mantenemos en Python como estaba, pero se podría optimizar aquí.
            
            raw_documents = []
            try:
                cursor = self.collection.find(mongo_query).sort("_id", -1).limit(limit)
                raw_documents = list(cursor)
            except Exception as sort_error:
                 # Fallback si falla el sort por memoria
                cursor = self.collection.find(mongo_query).limit(limit)
                raw_documents = list(cursor)
            
            all_norm_docs = [self._normalize_document(d) for d in raw_documents]
            
            if not all_norm_docs:
                return pd.DataFrame()
                
            # Ordenar por fecha descendente
            all_norm_docs.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)
            
            # Convertir a DataFrame historial plano
            df = self._parse_historical_flat(all_norm_docs)
            
            # Filtro de fechas en memoria (Pandas)
            if not df.empty and (start_date or end_date):
                if df['timestamp'].dt.tz is not None:
                        df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                
                if start_date:
                    if not isinstance(start_date, datetime): start_date = pd.to_datetime(start_date)
                    df = df[df['timestamp'] >= start_date]
                
                if end_date:
                    if not isinstance(end_date, datetime): end_date = pd.to_datetime(end_date)
                    df = df[df['timestamp'] <= end_date]
            
            return df
            
        except Exception as e:
            st.warning(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()

    # --- MÉTODOS DE CONFIGURACIÓN ---
    
    def _get_config_collection(self):
        if self.db is not None:
             return self.db[self.CONFIG_COLLECTION]
        return None

    def get_config(self, config_id: str = "sensor_thresholds") -> Optional[Dict[str, Any]]:
        coll = self._get_config_collection()
        if coll is None: return None
        try:
            return coll.find_one({"_id": config_id})
        except Exception:
            return None

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        coll = self._get_config_collection()
        if coll is None: return False
        try:
            config_data["_id"] = config_id
            config_data["last_updated"] = datetime.now().isoformat()
            result = coll.replace_one({"_id": config_id}, config_data, upsert=True)
            return result.acknowledged
        except Exception as e:
            st.error(f"Error al guardar config: {str(e)}")
            return False

    # --- MÉTODOS DE METADATOS DE DISPOSITIVOS ---
    
    def get_device_metadata(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el documento de metadatos de un dispositivo específico."""
        if self.devices_collection is None:
            return None
        try:
            return self.devices_collection.find_one({"_id": device_id})
        except Exception as e:
            print(f"Error al obtener metadata del dispositivo {device_id}: {e}")
            return None
    
    def get_all_devices_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los documentos de dispositivos como un diccionario."""
        if self.devices_collection is None:
            return {}
        try:
            devices = self.devices_collection.find({})
            # Convertir a dict con device_id como clave
            result = {}
            for dev in devices:
                dev_id = dev.get("_id")
                if dev_id:
                    result[dev_id] = dev
            return result
        except Exception as e:
            print(f"Error al obtener metadatos de dispositivos: {e}")
            return {}
    
    def update_device_metadata(self, device_id: str, metadata: Dict[str, Any]) -> bool:
        """Actualiza o crea el documento de metadatos de un dispositivo."""
        if self.devices_collection is None:
            return False
        try:
            metadata["_id"] = device_id
            metadata["last_updated"] = datetime.now().isoformat()
            result = self.devices_collection.replace_one(
                {"_id": device_id}, 
                metadata, 
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            st.error(f"Error al actualizar metadata del dispositivo: {str(e)}")
            return False
    
    def update_device_fields(self, device_id: str, fields: Dict[str, Any]) -> bool:
        """Actualiza campos específicos de un dispositivo usando $set (preserva otros campos)."""
        if self.devices_collection is None:
            return False
        try:
            result = self.devices_collection.update_one(
                {"_id": device_id},
                {"$set": fields},
                upsert=True  # Crear documento si no existe
            )
            return result.modified_count > 0 or result.matched_count > 0 or result.upserted_id is not None
        except Exception as e:
            st.error(f"Error al actualizar campos del dispositivo: {str(e)}")
            return False

    def delete_config(self, config_id: str) -> bool:
        coll = self._get_config_collection()
        if coll is None: return False
        try:
            result = coll.delete_one({"_id": config_id})
            return result.deleted_count > 0
        except Exception:
            return False

    # --- HELPERS DE DATAFRAME (Sin Cambios) ---
    
    def _rows_to_dataframe(self, norm_docs: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convierte docs YA normalizados a DataFrame para Dashboard."""
        processed = []
        for doc in norm_docs:
            processed.append({
                "device_id": doc["device_id"],
                "timestamp": doc["timestamp"],
                "location": doc["location"],
                "sensor_data": doc["sensors"], 
                "alerts": doc["alerts"]
            })
            
        df = pd.DataFrame(processed)
        if "timestamp" in df.columns and not df.empty:
             df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        return df

    def _parse_historical_flat(self, norm_docs: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convierte docs YA normalizados a estructura plana para Historial/Gráficas."""
        flat_data = []
        for doc in norm_docs:
            row = {
                "timestamp": doc["timestamp"],
                "device_id": doc["device_id"],
                "location": doc["location"],
            }
            # Aplanar sensores
            sensors = doc["sensors"]
            for name, val in sensors.items():
                # Manejar si el sensor es un objeto {value: ...} o valor directo
                if isinstance(val, dict):
                    row[name] = val.get("value")
                elif isinstance(val, (int, float)):
                    row[name] = val
                    
            flat_data.append(row)
        
        df = pd.DataFrame(flat_data)
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
            
        # Asegurar tipos numéricos para columnas de sensores
        cols = df.columns.drop(['timestamp', 'device_id', 'location'], errors='ignore')
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df