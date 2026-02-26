import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    # Defaults to localhost if not set in .env
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "careerprep_db")
    
    try:
        db.client = AsyncIOMotorClient(mongo_url)
        db.db = db.client[db_name]
        print(f"✅ Connected to MongoDB: {db_name}")
    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("🔒 MongoDB connection closed")