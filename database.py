# database.py
import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
from bson.objectid import ObjectId

# This loads your secret key from the .env file
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# This sets up the connection to your database
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["medical_app_db"]
    users_collection = db["users"]
    client.admin.command('ping')
    print("MongoDB connection successful.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None

def get_user_by_email(email: str):
    """Finds a user by their email address."""
    if not client: return None
    return users_collection.find_one({"email": email.lower()})

def create_user(name: str, age: int, email: str, language: str):
    """Creates a new user document in the database."""
    if not client: return None
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
    # Fetches and returns the complete new user profile
    return users_collection.find_one({"_id": result.inserted_id})

def update_user_history(user_id, history_list: list):
    """Finds a user by their _id and updates their past_history field."""
    if not client: return None
    
    # Use the $set operator to update the specific field in the document
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'past_history': history_list}}
    )
    print(f"Updated past history for user {user_id}")