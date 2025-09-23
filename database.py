# database.py
"""
MongoDB wrapper with a safe local JSON fallback.
Handles user creation, retrieval, and updates for the Medaid application.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
USE_MONGO = bool(MONGO_URI)

# Attempt to connect to MongoDB
if USE_MONGO:
    try:
        import pymongo
        from bson.objectid import ObjectId
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # Added timeout
        db = client.get_database(os.getenv("MONGO_DB", "medaid"))
        users_coll = db.users
        client.server_info() # Test connection
        print("✅ MongoDB connection successful.")
    except Exception as e:
        print(f"❌ Mongo init failed: {e}")
        USE_MONGO = False
else:
    print("ℹ️ MONGO_URI not found. Using local JSON file as a database fallback.")

# Local JSON fallback logic
LOCAL_DB = os.path.join(os.path.dirname(__file__), "local_db.json")
if not os.path.exists(LOCAL_DB):
    with open(LOCAL_DB, "w") as f:
        json.dump({"users": []}, f)

def _read_local():
    with open(LOCAL_DB, "r") as f: return json.load(f)

def _write_local(d):
    with open(LOCAL_DB, "w") as f: json.dump(d, f, default=str, indent=2)

def get_user_by_email(email: str):
    """Retrieves a user profile by their email address."""
    if not email: return None
    email_lower = email.lower()
    
    if USE_MONGO:
        user = users_coll.find_one({"email": email_lower})
        if user and user.get("_id"):
            user["_id"] = str(user["_id"])
        # Normalize past_history
        if user:
            ph = user.get("past_history", {})
            if isinstance(ph, list) or ph is None:
                user["past_history"] = {}
        return user
    
    # Local JSON fallback
    data = _read_local()
    user = next((u for u in data.get("users", []) if u.get("email", "").lower() == email_lower), None)
    if user:
        ph = user.get("past_history", {})
        if isinstance(ph, list) or ph is None:
            user["past_history"] = {}
    return user

def create_user(name: str, age: int, email: str, language: str = "English"):
    """Creates a new user with an empty, structured past_history."""
    if not name or not email: return None
    
    # Ensure past_history is initialized as a dictionary
    doc = {
        "name": name,
        "age": int(age),
        "email": email.lower(),
        "language": language,
        "past_history": {},
        "records": [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    if USE_MONGO:
        users_coll.insert_one(doc)
        return get_user_by_email(email)
    
    # Local JSON fallback
    data = _read_local()
    doc["_id"] = email.lower() # Use email as ID for local fallback
    data["users"].append(doc)
    _write_local(data)
    return doc

def update_user_history(user_id, history_dict: dict, session_record: dict = None):
    """
    Updates a user's past_history dictionary and optionally appends a new session record.
    """
    if not user_id: return False
    
    update_doc = {"$set": {"past_history": history_dict}}
    if session_record:
        update_doc["$push"] = {"records": session_record}
        
    if USE_MONGO:
        try:
            # Handle both string and ObjectId for user_id to prevent errors
            query_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            users_coll.update_one({"_id": query_id}, update_doc)
            return True
        except Exception as e:
            print(f"DB update error for user '{user_id}': {e}")
            return False
            
    # Local JSON fallback
    data = _read_local()
    for u in data.get("users", []):
        if u.get("_id") == user_id or u.get("email") == user_id:
            u["past_history"] = history_dict
            if session_record:
                u.setdefault("records", []).append(session_record)
            _write_local(data)
            return True
    return False

def update_user_report_data(user_id, report_data: dict):
    """Updates the report_data field for a specific user."""
    if not user_id: return False
    
    if USE_MONGO:
        try:
            query_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            users_coll.update_one({"_id": query_id}, {"$set": {"report_data": report_data}})
            return True
        except Exception as e:
            print(f"DB report data update error for user '{user_id}': {e}")
            return False

    # Local JSON fallback
    data = _read_local()
    for u in data.get("users",[]):
        if u.get("_id") == user_id or u.get("email") == user_id:
            u["report_data"] = report_data
            _write_local(data)
            return True
    return False