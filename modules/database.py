import os
import time
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import certifi
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# --- PATRÓN SINGLETON (CONEXIÓN ROBUSTA) ---
@st.cache_resource(ttl=3600, show_spinner=False)
def get_mongo_client() -> Optional[MongoClient]:
    uri = os.getenv("MONGO_URI")
    if not uri:
        st.error("Error Crítico: MONGO_URI no encontrado en .env")
        return None

    try:
        client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=20000,
            serverSelectionTimeoutMS=20000, 
            socketTimeoutMS=20000,
            maxPoolSize=10,
            minPoolSize=1,
            retryWrites=True # Reintentos de escritura automáticos de Mongo
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Error fatal de conexión a MongoDB: {str(e)}")
        return None

class DatabaseConnection:
    CONFIG_COLLECTION = "system_config"

    def __init__(self):
        self._db_name = os.getenv("MONGO_DB")
        self._collection_name = os.getenv("MONGO_COLLECTION")
        self._client = get_mongo_client()

    # --- MÉTODO PARA DASHBOARD (Estrategia Simple y Probada) ---
    def get_latest_by_device(self, retries: int = 3) -> pd.DataFrame:
        if not self._client: return pd.DataFrame()

        if not self._client: return pd.DataFrame()
        
        last_error = None
        for attempt in range(3):
            try:
                db = self._client[self._db_name]
                collection = db[self._collection_name]
                
                cursor = collection.find({}).sort("timestamp", -1).limit(2000)
                documents = list(cursor)
                
                seen_devices = set()
                latest_docs = []
                
                for doc in documents:
                    dev_id = doc.get("device_id")
                    if not dev_id: dev_id = doc.get("metadata", {}).get("device_id", "unknown")
                    
                    if dev_id not in seen_devices:
                        seen_devices.add(dev_id)
                        latest_docs.append(doc)
                
                return self._process_dashboard_data(latest_docs)
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                last_error = e
                time.sleep(1 * (attempt+1))
                continue
            except Exception as e:
                print(f"Error fetching dashboard data: {str(e)}")
                return pd.DataFrame()
                
        # Si falla todo
        print(f"Dashboard Timeout tras 3 intentos: {str(last_error)}")
        return pd.DataFrame()

    def get_latest_for_single_device(self, device_id: str) -> pd.DataFrame:
        """Obtiene el último dato de UN solo dispositivo para actualización parcial."""
        if not self._client: return pd.DataFrame()
        try:
            db = self._client[self._db_name]
            collection = db[self._collection_name]
            
            doc = collection.find_one(
                {"device_id": device_id},
                sort=[("timestamp", -1)]
            )
            
            if not doc: return pd.DataFrame()
            return self._process_dashboard_data([doc])
        except Exception as e:
            print(f"Error refreshing device {device_id}: {str(e)}")
            return pd.DataFrame()

    # --- MÉTODOS PARA HISTORIAL Y GRÁFICOS ---
    def fetch_data(self, start_date=None, end_date=None, device_ids=None, limit=5000) -> pd.DataFrame:
        if not self._client: return pd.DataFrame()
        
        last_error = None
        for attempt in range(3): # 3 Intentos explícitos
            try:
                db = self._client[self._db_name]
                collection = db[self._collection_name]
                
                # ... construcción de pipeline ...
                mongo_query = {}
                if device_ids:
                    mongo_query["device_id"] = {"$in": device_ids}
                
                pipeline = [
                    {"$match": mongo_query},
                    {"$sort": {"_id": -1}}, # Optimización: Usar índice _id
                    {"$limit": limit}
                ]
                
                cursor = collection.aggregate(pipeline, allowDiskUse=True)
                documents = list(cursor)
                
                if not documents:
                    return pd.DataFrame()
                
                # Parsing y filtrado
                df = self._parse_historical_documents(documents)
                
                # Filtro Pandas memory
                if not df.empty and (start_date or end_date):
                    if df['timestamp'].dt.tz is not None:
                         df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                    
                    if start_date:
                        if not isinstance(start_date, datetime): start_date = pd.to_datetime(start_date)
                        df = df[df['timestamp'] >= start_date]
                    
                    if end_date:
                        if not isinstance(end_date, datetime): end_date = pd.to_datetime(end_date)
                        df = df[df['timestamp'] <= end_date]
                
                return df # Éxito, salir
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                last_error = e
                time.sleep(1 * (attempt + 1)) # Backoff 1s, 2s, 3s
                continue # Reintentar
            except Exception as e:
                st.error(f"Error lógico (Query): {str(e)}")
                return pd.DataFrame() # Error no recuperable
        
        # Si llega aquí, falló 3 veces
        st.error(f"Error de conexión persistente tras 3 intentos: {str(last_error)}")
        return pd.DataFrame()



    # --- MÉTODOS DE CONFIGURACIÓN ---
    def get_config(self, config_id: str = "sensor_thresholds") -> Optional[Dict[str, Any]]:
        if not self._client: return None
        try:
            db = self._client[self._db_name]
            collection = db[self.CONFIG_COLLECTION]
            return collection.find_one({"_id": config_id})
        except Exception:
            return None

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        if not self._client: return False
        try:
            db = self._client[self._db_name]
            collection = db[self.CONFIG_COLLECTION]
            
            config_data["_id"] = config_id
            config_data["last_updated"] = datetime.now().isoformat()
            
            result = collection.replace_one(
                {"_id": config_id},
                config_data,
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            st.error(f"Error al guardar config: {str(e)}")
            return False

    def delete_config(self, config_id: str) -> bool:
        if not self._client: return False
        try:
            db = self._client[self._db_name]
            collection = db[self.CONFIG_COLLECTION]
            result = collection.delete_one({"_id": config_id})
            return result.deleted_count > 0
        except Exception:
            return False

    # --- PROCESADORES DE DATOS ---
    
    def _process_dashboard_data(self, documents: List[Dict[str, Any]]) -> pd.DataFrame:
        processed = []
        for doc in documents:
            raw_ts = doc.get("timestamp")
            final_ts = raw_ts

            # Lógica Robusta de Parsing de Fechas
            try:
                if isinstance(raw_ts, (int, float)):
                    # Detectar ms vs segundos (año 2000 ~9.4e8)
                    if raw_ts > 1e11: 
                        final_ts = pd.to_datetime(raw_ts, unit='ms').to_pydatetime()
                    else:
                        final_ts = pd.to_datetime(raw_ts, unit='s').to_pydatetime()
                elif isinstance(raw_ts, str):
                    # Parseo ISO estándar
                    final_ts = pd.to_datetime(raw_ts, errors='coerce')
                    if not pd.isna(final_ts):
                         final_ts = final_ts.to_pydatetime()
                    else:
                         final_ts = None
            except Exception:
                # Si falla, dejarlo como None
                final_ts = None

            processed.append({
                "device_id": doc.get("device_id", "Desconocido"),
                "timestamp": final_ts,
                "location": doc.get("location", "Sin Asignar"),
                "sensor_data": doc.get("sensors", {}),
                "alerts": doc.get("alerts", [])
            })
        
        df = pd.DataFrame(processed)
        # Asegurar tipo datetime
        if "timestamp" in df.columns and not df.empty:
             df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
             
        return df

    def _parse_historical_documents(self, documents: List[Dict[str, Any]]) -> pd.DataFrame:
        parsed_data = []
        for doc in documents:
            row = {
                "timestamp": doc.get("timestamp"),
                "device_id": doc.get("device_id"),
                "location": doc.get("location", "unknown"),
            }
            sensors = doc.get("sensors", {})
            for name, data in sensors.items():
                if isinstance(data, dict):
                    row[name] = data.get("value")
                elif isinstance(data, (int, float)):
                    row[name] = data
            
            parsed_data.append(row)
        
        df = pd.DataFrame(parsed_data)
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
            
        cols = df.columns.drop(['timestamp', 'device_id', 'location'], errors='ignore')
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df