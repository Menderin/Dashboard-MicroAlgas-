"""
Generador de datos de prueba para Biofloc Monitor.
Crea registros simulados en MongoDB para testing y demostraciones.
Incluye dispositivos con diferentes cantidades de sensores.
"""

import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

# Cargar entorno desde la raiz del proyecto
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")
DEMO_COLLECTION = "SensorReadings_DEMO"


def generate_mock_data():
    """Genera datos de prueba con variedad de sensores por dispositivo."""
    if not URI:
        print("[ERROR] No se encontro MONGO_URI en .env")
        return

    print("[INFO] Conectando a MongoDB...")
    try:
        client = MongoClient(URI, tlsCAFile=certifi.where())
        db = client[DB_NAME]
        collection = db[DEMO_COLLECTION]
        client.admin.command('ping')
    except Exception as e:
        print(f"[ERROR] Error de conexion: {e}")
        return

    # Limpiar datos demo anteriores
    collection.delete_many({})
    db["system_config"].delete_many({})
    print(f"[INFO] Coleccion '{DEMO_COLLECTION}' limpiada.")

    # Configuracion de dispositivos con DIFERENTES cantidades de sensores
    devices_config = [
        # --- DISPOSITIVOS CON POCOS SENSORES (1-2) ---
        {"id": "Sensor-Simple-01", "status": "ok", "loc": "Entrada", 
         "sensors": ["temperature"]},
        {"id": "Sensor-Basico-02", "status": "ok", "loc": "Pasillo", 
         "sensors": ["temperature", "humidity"]},
        {"id": "Monitor-pH", "status": "warning", "loc": "Laboratorio", 
         "sensors": ["ph"]},
        
        # --- DISPOSITIVOS ESTANDAR (3-4 sensores) ---
        {"id": "Tanque-A1 (Camarones)", "status": "ok", "loc": "Invernadero 1", 
         "sensors": ["temperature", "ph", "do"]},
        {"id": "Tanque-A2 (Camarones)", "status": "ok", "loc": "Invernadero 1", 
         "sensors": ["temperature", "ph", "do", "ammonia"]},
        {"id": "Tanque-B1 (Tilapia)", "status": "warning", "loc": "Invernadero 2", 
         "sensors": ["temperature", "ph", "do", "turbidity"]},
        {"id": "Biofloc-Principal", "status": "ok", "loc": "Zona Tesis", 
         "sensors": ["temperature", "ph", "do", "ammonia"]},
        
        # --- DISPOSITIVOS CON MUCHOS SENSORES (5-8) ---
        {"id": "Estacion-Completa-01", "status": "ok", "loc": "Centro Control", 
         "sensors": ["temperature", "ph", "do", "ammonia", "nitrite", "salinity"]},
        {"id": "BioReactor-Avanzado", "status": "critical", "loc": "Laboratorio", 
         "sensors": ["temperature", "ph", "do", "ammonia", "nitrite", "nitrate", "tds"]},
        {"id": "Monitor-Multiparametro", "status": "ok", "loc": "Exterior", 
         "sensors": ["temperature", "humidity", "ph", "do", "conductivity", "salinity", "turbidity", "chlorophyll"]},
        
        # --- DISPOSITIVO OFFLINE ---
        {"id": "Sensor-Desconectado", "status": "offline", "loc": "Bodega", 
         "sensors": ["temperature", "ph"]},
        
        # --- DISPOSITIVO CRITICO ---
        {"id": "Tanque-Emergencia", "status": "critical", "loc": "Cuarentena", 
         "sensors": ["temperature", "ph", "do", "ammonia", "nitrite"]},
    ]

    # Valores base para cada tipo de sensor
    sensor_values = {
        "temperature": {"base": 28.0, "range": 2.0, "critical_high": 42.0, "warning_high": 32.0},
        "ph": {"base": 7.5, "range": 0.3, "critical_high": 9.5, "warning_high": 8.5},
        "do": {"base": 6.0, "range": 1.0, "critical_low": 2.0, "warning_low": 4.0},
        "ammonia": {"base": 0.1, "range": 0.05, "critical_high": 1.0, "warning_high": 0.5},
        "nitrite": {"base": 0.05, "range": 0.02, "critical_high": 0.5, "warning_high": 0.25},
        "nitrate": {"base": 20.0, "range": 5.0, "critical_high": 100.0, "warning_high": 50.0},
        "humidity": {"base": 65.0, "range": 10.0},
        "salinity": {"base": 35.0, "range": 2.0},
        "turbidity": {"base": 15.0, "range": 5.0},
        "tds": {"base": 500.0, "range": 50.0},
        "conductivity": {"base": 1200.0, "range": 100.0},
        "chlorophyll": {"base": 8.0, "range": 2.0},
    }

    print(f"[INFO] Generando datos para {len(devices_config)} dispositivos...")
    
    records = []
    end_time = datetime.now()

    for dev in devices_config:
        # Dispositivos offline tienen datos antiguos
        if dev['status'] == 'offline':
            last_seen = end_time - timedelta(days=3)
            current_time = last_seen - timedelta(hours=2)
        else:
            current_time = end_time - timedelta(hours=24)
            last_seen = end_time

        while current_time <= last_seen:
            # Generar valores para cada sensor del dispositivo
            sensors_data = {}
            for sensor_name in dev['sensors']:
                config = sensor_values.get(sensor_name, {"base": 50.0, "range": 10.0})
                base = config["base"]
                variation = config["range"]
                
                # Modificar segun estado del dispositivo
                if dev['status'] == 'ok':
                    value = base + random.uniform(-variation, variation)
                elif dev['status'] == 'warning':
                    # Valor en zona de alerta
                    if "warning_high" in config:
                        value = config["warning_high"] + random.uniform(0, 1)
                    elif "warning_low" in config:
                        value = config["warning_low"] - random.uniform(0, 0.5)
                    else:
                        value = base + random.uniform(-variation, variation)
                elif dev['status'] == 'critical':
                    # Valor en zona critica
                    if "critical_high" in config:
                        value = config["critical_high"] + random.uniform(0, 2)
                    elif "critical_low" in config:
                        value = config["critical_low"] - random.uniform(0, 1)
                    else:
                        value = base + random.uniform(-variation, variation)
                else:
                    value = base + random.uniform(-variation, variation)
                
                sensors_data[sensor_name] = round(value, 2)
            
            record = {
                "device_id": dev["id"],
                "timestamp": current_time,
                "location": dev["loc"],
                "sensors": sensors_data
            }
            records.append(record)
            current_time += timedelta(minutes=60)
            
        # Agregar dato MUY RECIENTE para mantener dispositivos online
        if dev['status'] != 'offline':
            # Recalcular sensores para el ultimo registro
            sensors_data = {}
            for sensor_name in dev['sensors']:
                config = sensor_values.get(sensor_name, {"base": 50.0, "range": 10.0})
                base = config["base"]
                variation = config["range"]
                
                if dev['status'] == 'ok':
                    value = base + random.uniform(-variation, variation)
                elif dev['status'] == 'warning':
                    if "warning_high" in config:
                        value = config["warning_high"] + random.uniform(0, 1)
                    else:
                        value = base + variation * 1.5
                elif dev['status'] == 'critical':
                    if "critical_high" in config:
                        value = config["critical_high"] + random.uniform(0, 2)
                    else:
                        value = base + variation * 3
                else:
                    value = base + random.uniform(-variation, variation)
                
                sensors_data[sensor_name] = round(value, 2)
            
            records.append({
                "device_id": dev["id"],
                "timestamp": datetime.now(),
                "location": dev["loc"],
                "sensors": sensors_data
            })

    # Insertar datos en MongoDB
    if records:
        try:
            collection.insert_many(records)
            print(f"[OK] {len(records)} registros insertados en '{DEMO_COLLECTION}'.")
            
            current_coll = os.getenv('MONGO_COLLECTION', 'SensorReadings')
            
            print("\n" + "="*60)
            print("   MODO DEMOSTRACION - DISPOSITIVOS GENERADOS")
            print("="*60)
            print("\n  POCOS SENSORES (1-2):")
            print("    - Sensor-Simple-01: solo temperatura")
            print("    - Sensor-Basico-02: temperatura + humedad")
            print("    - Monitor-pH: solo pH")
            print("\n  ESTANDAR (3-4 sensores):")
            print("    - Tanques A1, A2, B1, Biofloc-Principal")
            print("\n  MUCHOS SENSORES (5-8):")
            print("    - Estacion-Completa-01: 6 sensores")
            print("    - BioReactor-Avanzado: 7 sensores")
            print("    - Monitor-Multiparametro: 8 sensores")
            print("\n" + "="*60)
            print(f"\n1. Cambia en .env: MONGO_COLLECTION={DEMO_COLLECTION}")
            print(f"2. Refresca el Dashboard")
            print(f"\nPara volver: MONGO_COLLECTION={current_coll}")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"[ERROR] Error insertando datos: {e}")
    else:
        print("[WARN] No se generaron registros.")


if __name__ == "__main__":
    generate_mock_data()
