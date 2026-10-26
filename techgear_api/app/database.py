import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["techgear"]
productos_collection = db["productos"]
pedidos_collection = db["pedidos"]
usuarios_collection = db["usuarios"]