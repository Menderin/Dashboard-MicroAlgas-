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
# Ahora soporta cachear multiples clientes por URI
@st.cache_resource(ttl=3600, show_spinner=False)
def get_mongo_client(uri: str) -> Optional[MongoClient]:
    if not uri: return None
    try:
        client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=10000, 
            serverSelectionTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5,
            minPoolSize=1,
            retryWrites=True,
            tz_aware=True # IMPORTANTE: Recuperar fechas como UTC-aware
        )
        # Ping rapido para validar
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Error conexión MongoDB ({uri[:20]}...): {str(e)}")
        return None

class DatabaseConnection:
    CONFIG_COLLECTION = "system_config"

    def __init__(self):
        self.sources = []
        
        # 1. Fuente Principal
        uri1 = os.getenv("MONGO_URI")
        db1 = os.getenv("MONGO_DB")
        coll1 = os.getenv("MONGO_COLLECTION")
        
        if uri1 and db1 and coll1:
            client1 = get_mongo_client(uri1)
            if client1:
                self.sources.append({
                    "name": "Primary",
                    "client": client1,
                    "db": db1,
                    "coll": coll1
                })
        
        # 2. Fuente Secundaria (Partner)
        uri2 = os.getenv("MONGO_URI_2")
        db2 = os.getenv("MONGO_DB_2")
        coll2 = os.getenv("MONGO_COLLECTION_2")
        
        if uri2 and db2 and coll2:
            client2 = get_mongo_client(uri2)
            if client2:
                self.sources.append({
                    "name": "Secondary",
                    "client": client2,
                    "db": db2,
                    "coll": coll2
                })

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
            
        return {
            "device_id": dev_id,
            "timestamp": final_ts,
            "location": doc.get("location", "Sin Asignar"),
            "sensors": sensors,
            "alerts": doc.get("alerts", []),
            "_source_id": oid 
        }

    # --- MÉTODO PARA DASHBOARD (Multi-DB) ---
    def get_latest_by_device(self, retries: int = 2) -> pd.DataFrame:
        if not self.sources: return pd.DataFrame()
        
        all_docs = []
        seen_devices = set()
        
        # Iterar sobre todas las fuentes configuradas
        for source in self.sources:
            try:
                db = source["client"][source["db"]]
                collection = db[source["coll"]]
                
                cursor = collection.find({}).sort("timestamp", -1).limit(1000) # Limitamos por fuente
                documents = list(cursor)
                
                for raw_doc in documents:
                    norm_doc = self._normalize_document(raw_doc)
                    dev_id = norm_doc["device_id"]
                    
                    # Prioridad: el primero que llega gana (usualmente el de la fuente principal si iteration order es fijo)
                    # O podrias querer ver duplicados si tienen mismo ID pero diferente fuente? 
                    # Asumiremos IDs unicos globales o que queremos unificar
                    if dev_id and dev_id != "unknown" and dev_id not in seen_devices:
                        seen_devices.add(dev_id)
                        all_docs.append(norm_doc)
                        
            except Exception as e:
                print(f"Error fetching from source {source['name']}: {str(e)}")
                continue

        return self._rows_to_dataframe(all_docs)

    def get_latest_for_single_device(self, device_id: str) -> pd.DataFrame:
        """Busca el dispositivo en todas las fuentes hasta encontrarlo."""
        if not self.sources: return pd.DataFrame()
        
        for source in self.sources:
            try:
                db = source["client"][source["db"]]
                collection = db[source["coll"]]
                
                query = {
                    "$or": [
                        {"device_id": device_id},
                        {"dispositivo_id": device_id}
                    ]
                }
                
                doc = collection.find_one(query, sort=[("timestamp", -1)])
                if doc:
                    norm_doc = self._normalize_document(doc)
                    return self._rows_to_dataframe([norm_doc])
                    
            except Exception:
                continue
                
        return pd.DataFrame()

    # --- MÉTODOS PARA HISTORIAL Y GRÁFICOS (Multi-DB Aggregation) ---
    def fetch_data(self, start_date=None, end_date=None, device_ids=None, limit=5000) -> pd.DataFrame:
        if not self.sources: return pd.DataFrame()
        
        all_norm_docs = []
        
        # Distribuir limite entre fuentes para no sobrecargar
        limit_per_source = limit // len(self.sources) + 100
        
        for source in self.sources:
            try:
                db = source["client"][source["db"]]
                collection = db[source["coll"]]
                
                mongo_query = {}
                if device_ids:
                    mongo_query["$or"] = [
                        {"device_id": {"$in": device_ids}},
                        {"dispositivo_id": {"$in": device_ids}}
                    ]
                
                pipeline = [
                    {"$match": mongo_query},
                    {"$sort": {"_id": -1}},
                    {"$limit": limit_per_source}
                ]
                
                cursor = collection.aggregate(pipeline, allowDiskUse=True)
                raw_documents = list(cursor)
                
                for d in raw_documents:
                    all_norm_docs.append(self._normalize_document(d))
                    
            except Exception as e:
                st.warning(f"Error parcial obteniendo datos de {source['name']}: {str(e)}")
                continue
        
        if not all_norm_docs:
            return pd.DataFrame()
            
        # Ordenar todo lo combinado por fecha descendente
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

    # --- MÉTODOS DE CONFIGURACIÓN (Solo en Fuente Principal) ---
    # Por seguridad y simplicidad, guardamos configs solo en la DB principal
    
    def _get_primary_collection(self, coll_name):
        if not self.sources: return None
        # Asumimos que la primera fuente es la principal (donde guardamos configs)
        source = self.sources[0]
        try:
             return source["client"][source["db"]][coll_name]
        except:
             return None

    def get_config(self, config_id: str = "sensor_thresholds") -> Optional[Dict[str, Any]]:
        coll = self._get_primary_collection(self.CONFIG_COLLECTION)
        if coll is None: return None
        try:
            return coll.find_one({"_id": config_id})
        except Exception:
            return None

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        coll = self._get_primary_collection(self.CONFIG_COLLECTION)
        if coll is None: return False
        try:
            config_data["_id"] = config_id
            config_data["last_updated"] = datetime.now().isoformat()
            result = coll.replace_one({"_id": config_id}, config_data, upsert=True)
            return result.acknowledged
        except Exception as e:
            st.error(f"Error al guardar config: {str(e)}")
            return False

    def delete_config(self, config_id: str) -> bool:
        coll = self._get_primary_collection(self.CONFIG_COLLECTION)
        if coll is None: return False
        try:
            result = coll.delete_one({"_id": config_id})
            return result.deleted_count > 0
        except Exception:
            return False

    # --- HELPERS DE DATAFRAME ---
    
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