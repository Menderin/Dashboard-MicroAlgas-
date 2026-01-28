import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

if not all([MONGO_URI, MONGO_DB, MONGO_COLLECTION]):
    raise ValueError("Variables de entorno no cargadas")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
col = db[MONGO_COLLECTION]

docs = list(col.find({}, {
    "_id": 0,
    "fecha": "$timestamp",
    "dispositivo": "$device_id",
    "temperatura": "$sensors.temperature.value",
    "ph": "$sensors.ph.value"
}))

df = pd.DataFrame(docs)

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", utc=True)
df["fecha"] = df["fecha"].dt.tz_convert(None)

df.to_excel("telemetria_limpia.xlsx", index=False)

print("Archivo generado: telemetria_limpia.xlsx")
print(df.head())
