# database.py
import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
from bson.objectid import ObjectId
import numpy as np

# --- Load Mongo URI ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# --- Setup MongoDB Connection ---
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["medical_app_db"]
    users_collection = db["users"]
    client.admin.command('ping')
    print("✅ MongoDB connection successful.")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    client = None


# --- Utility Cleaner ---
def clean_for_mongo(obj):
    """Recursively convert numpy and non-serializable objects into MongoDB-safe types."""
    if isinstance(obj, dict):
        return {k: clean_for_mongo(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_mongo(v) for v in obj]
    elif isinstance(obj, np.generic):  # np.float32, np.int64, etc.
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


# --- DB Functions ---
def get_user_by_email(email: str):
    """Finds a user by their email address."""
    if not client: 
        return None
    return users_collection.find_one({"email": email.lower()})


def create_user(name: str, age: int, email: str, language: str):
    """Creates a new user document in the database."""
    if not client: 
        return None
    user_document = {
        "name": name,
        "age": age,
        "email": email.lower(),
        "language": language,
        "past_history": [],  # Initializes empty history for a new user
        "records": [],       # Initializes empty records for the Health Passport
        "created_at": datetime.now()
    }
    result = users_collection.insert_one(user_document)
    return users_collection.find_one({"_id": result.inserted_id})


def update_user_history(user_id, history_list: list, session_record: dict):
    """Updates user's past_history and adds a new session record."""
    if not client: 
        return None
    
    # ✅ Clean before saving
    cleaned_session_record = clean_for_mongo(session_record)
    cleaned_history = clean_for_mongo(history_list)

    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {
            '$set': {'past_history': cleaned_history},
            '$push': {
                'records': {
                    'timestamp': datetime.now(),
                    'session_data': cleaned_session_record
                }
            }
        }
    )
    print(f"✅ Updated past history and added session record for user {user_id}")


def update_user_report_data(user_id, report_data: dict):
    """Updates user's report_data field."""
    if not client: 
        return None
    
    # ✅ Clean before saving
    cleaned_report_data = clean_for_mongo(report_data)

    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'report_data': cleaned_report_data}}
    )
    print(f"✅ Updated report data for user {user_id}")
