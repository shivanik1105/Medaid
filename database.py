# database.py
"""
MongoDB wrapper with safe local JSON fallback.
Functions:
 - get_user_by_email
 - create_user
 - update_user_history
 - update_user_report_data
"""

import os, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
USE_MONGO = bool(MONGO_URI)

if USE_MONGO:
    try:
        import pymongo
        client = pymongo.MongoClient(MONGO_URI)
        db = client.get_database(os.getenv("MONGO_DB","medaid"))
        users_coll = db.users
    except Exception as e:
        print("Mongo init failed:", e)
        USE_MONGO = False

# local fallback file
LOCAL_DB = os.path.join(os.path.dirname(__file__), "local_db.json")
if not os.path.exists(LOCAL_DB):
    with open(LOCAL_DB,"w") as f:
        json.dump({"users":[]}, f)

def _read_local():
    with open(LOCAL_DB,"r") as f: return json.load(f)
def _write_local(d): 
    with open(LOCAL_DB,"w") as f: json.dump(d,f,default=str, indent=2)

def get_user_by_email(email: str):
    if not email: return None
    if USE_MONGO:
        u = users_coll.find_one({"email": email.lower()})
        if u: 
            u["_id"] = str(u["_id"])
        return u
    data = _read_local()
    for u in data.get("users",[]):
        if u.get("email","").lower() == email.lower():
            return u
    return None

def create_user(name: str, age: int, email: str, language: str="English"):
    doc = {"name": name, "age": int(age), "email": email.lower(), "language": language, "past_history": [], "records": [], "created_at": datetime.utcnow().isoformat()}
    if USE_MONGO:
        res = users_coll.insert_one(doc)
        return users_coll.find_one({"_id": res.inserted_id})
    data = _read_local()
    doc["_id"] = email.lower()
    data["users"].append(doc)
    _write_local(data)
    return doc

def update_user_history(user_id, history_list, session_record):
    if USE_MONGO:
        try:
            users_coll.update_one({"_id": user_id},{"$set":{"past_history": history_list}, "$push": {"records": session_record}})
            return True
        except Exception as e:
            print("DB update error", e); return False
    data = _read_local()
    for i,u in enumerate(data.get("users",[])):
        if u.get("_id") == user_id or u.get("email")==user_id:
            u["past_history"] = history_list
            u.setdefault("records",[]).append(session_record)
            _write_local(data)
            return True
    return False

def update_user_report_data(user_id, report_data):
    if not user_id: return False
    if USE_MONGO:
        users_coll.update_one({"_id": user_id},{"$set":{"report_data": report_data}})
        return True
    data = _read_local()
    for i,u in enumerate(data.get("users",[])):
        if u.get("_id") == user_id or u.get("email")==user_id:
            u["report_data"] = report_data
            _write_local(data); return True
    return False
