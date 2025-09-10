# test_google_verbose.py
import os, requests, sys
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    print("ERROR: GOOGLE_API_KEY not found in env")
    sys.exit(1)

pincode = "411046"   # change to the pincode you're testing
print("Using API key (first 8 chars):", API_KEY[:8] + "..." if API_KEY else None)

def pretty(resp):
    import json
    print(json.dumps(resp, indent=2, ensure_ascii=False))

# 1) Geocode
g_url = "https://maps.googleapis.com/maps/api/geocode/json"
g_params = {"address": pincode, "key": API_KEY}
g = requests.get(g_url, params=g_params, timeout=10)
print("GEOCODE HTTP", g.status_code)
pretty(g.json())

# 2) If geocode ok, call Places
if g.json().get("status") == "OK":
    loc = g.json()["results"][0]["geometry"]["location"]
    lat, lng = loc["lat"], loc["lng"]
    print("lat,lng:", lat, lng)
    p_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    p_params = {"location": f"{lat},{lng}", "radius": 5000, "type": "hospital", "key": API_KEY}
    p = requests.get(p_url, params=p_params, timeout=10)
    print("PLACES HTTP", p.status_code)
    pretty(p.json())
else:
    print("Geocode failed; skipping places request.")
