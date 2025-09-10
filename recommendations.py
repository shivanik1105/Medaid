# recommendations.py
"""
Robust facility lookup helper.

- Prefer Google (Geocoding + Places) if GOOGLE_PLACES_API_KEY present and enabled.
- If Google fails or is not available, fallback to OpenStreetMap (Nominatim) + Overpass.
- Simple file-based caching to reduce repeated API calls.
- Returns list of dicts: {name,address,phone,rating,lat,lng,distance_km,maps_url}
"""

import os
import json
import math
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Env keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
MAPS_EMBED_KEY = os.getenv("MAPS_EMBED_KEY", "") or GOOGLE_PLACES_API_KEY

# Simple persistent cache (file)
CACHE_DIR = Path(os.getenv("RECO_CACHE_DIR", ".reco_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = int(os.getenv("RECO_CACHE_TTL_SECS", 60 * 60 * 6))  # 6 hours

def _cache_get(key):
    path = CACHE_DIR / (key.replace("/", "_").replace(" ", "_") + ".json")
    if not path.exists(): 
        return None
    try:
        data = json.loads(path.read_text(encoding="utf8"))
        if time.time() - data.get("_ts", 0) > CACHE_TTL:
            return None
        return data.get("value")
    except Exception:
        return None

def _cache_set(key, value):
    path = CACHE_DIR / (key.replace("/", "_").replace(" ", "_") + ".json")
    try:
        obj = {"_ts": time.time(), "value": value}
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf8")
    except Exception:
        pass

# Helpers
def _haversine_km(lat1, lon1, lat2, lon2):
    # approximate distance in km
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Google path
def _google_geocode(address):
    if not GOOGLE_PLACES_API_KEY:
        return None
    cache_key = f"geocode_google_{address}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_PLACES_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            out = {"lat": loc["lat"], "lng": loc["lng"], "raw": data["results"][0]}
            _cache_set(cache_key, out)
            return out
        # store failure to avoid tight retry loops
        _cache_set(cache_key, None)
        return None
    except Exception:
        return None

def _google_places_nearby(lat, lng, radius=10000, place_type="hospital"):
    if not GOOGLE_PLACES_API_KEY:
        return []
    cache_key = f"places_google_{lat}_{lng}_{radius}_{place_type}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{lat},{lng}", "radius": radius, "type": place_type, "key": GOOGLE_PLACES_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        out = []
        if data.get("status") in ("OK", "ZERO_RESULTS"):
            for p in data.get("results", [])[:20]:
                loc = p.get("geometry", {}).get("location", {})
                item = {
                    "name": p.get("name"),
                    "address": p.get("vicinity") or p.get("formatted_address") or "",
                    "rating": p.get("rating"),
                    "lat": loc.get("lat"),
                    "lng": loc.get("lng"),
                    "place_id": p.get("place_id"),
                    "maps_url": f"https://www.google.com/maps/place/?q=place_id:{p.get('place_id')}"
                }
                out.append(item)
        _cache_set(cache_key, out)
        return out
    except Exception:
        return []

# OSM fallback path
def _nominatim_geocode(address):
    cache_key = f"geocode_nominatim_{address}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "Medaid/1.0 (contact@example.com)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if data:
            out = {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"]), "raw": data[0]}
            _cache_set(cache_key, out)
            return out
        _cache_set(cache_key, None)
        return None
    except Exception:
        return None

def _overpass_find_hospitals(lat, lng, radius_m=10000):
    # Overpass QL: amenity=hospital or healthcare=clinic/doctor
    cache_key = f"overpass_{lat}_{lng}_{radius_m}"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lng});
      way["amenity"="hospital"](around:{radius_m},{lat},{lng});
      node["healthcare"="clinic"](around:{radius_m},{lat},{lng});
      node["healthcare"="doctors"](around:{radius_m},{lat},{lng});
    );
    out center 20;
    """
    url = "https://overpass-api.de/api/interpreter"
    try:
        resp = requests.post(url, data=query, timeout=30)
        data = resp.json()
        out = []
        for el in data.get("elements", [])[:50]:
            if el.get("type") == "node":
                latp = el.get("lat")
                lngp = el.get("lon")
            else:
                c = el.get("center") or {}
                latp = c.get("lat")
                lngp = c.get("lon")
            name = el.get("tags", {}).get("name") or el.get("tags", {}).get("official_name") or "Hospital"
            addr_parts = []
            tags = el.get("tags", {})
            for k in ("addr:street","addr:housenumber","addr:city","addr:postcode"):
                if tags.get(k):
                    addr_parts.append(tags.get(k))
            address = ", ".join(addr_parts) if addr_parts else (tags.get("operator") or "")
            maps_url = f"https://www.openstreetmap.org/?mlat={latp}&mlon={lngp}#map=16/{latp}/{lngp}"
            out.append({
                "name": name,
                "address": address,
                "lat": latp,
                "lng": lngp,
                "maps_url": maps_url
            })
        _cache_set(cache_key, out)
        return out
    except Exception:
        return []

# Public API
def get_recommendations(risk_level, user_city="", user_state="", user_pincode=""):
    """
    Returns a list of facility dicts. Accepts either city or pincode (or both).
    """
    # Build location query
    location_query = ""
    # prefer pincode when provided because user typed it in form
    if user_pincode:
        location_query = str(user_pincode)
        if user_city and not any(c.isdigit() for c in user_city):
            # if both given prefer "city, pincode"
            location_query = f"{user_city}, {user_pincode}"
    elif user_city:
        location_query = str(user_city)
    elif user_state:
        location_query = user_state
    else:
        return []

    key_for_cache = f"reco_{location_query}"
    cached = _cache_get(key_for_cache)
    if cached is not None:
        return cached

    results = []

    # 1) Try Google path if key available
    if GOOGLE_PLACES_API_KEY:
        geo = _google_geocode(location_query)
        if geo:
            lat = geo["lat"]; lng = geo["lng"]
            places = _google_places_nearby(lat, lng, radius=10000, place_type="hospital")
            if places:
                for p in places:
                    dist = None
                    try:
                        dist = _haversine_km(lat, lng, float(p.get("lat")), float(p.get("lng")))
                        p["distance_km"] = round(dist, 1)
                    except Exception:
                        p["distance_km"] = None
                    # Add phone/rating if we want to call Place Details (optional)
                    results.append(p)
                _cache_set(key_for_cache, results)
                return results
            # if Google returned ZERO_RESULTS we may still continue to OSM fallback

    # 2) OSM fallback: geocode with Nominatim
    geo = _nominatim_geocode(location_query)
    if geo:
        lat = geo["lat"]; lng = geo["lng"]
        over = _overpass_find_hospitals(lat, lng, radius_m=10000)
        if over:
            out = []
            for p in over:
                try:
                    p["distance_km"] = round(_haversine_km(lat, lng, float(p.get("lat")), float(p.get("lng"))), 1)
                except Exception:
                    p["distance_km"] = None
                out.append(p)
            _cache_set(key_for_cache, out)
            return out

    # 3) Last-resort: if neither service works, return helpful generic list depending on risk level
    fallback = []
    if "High" in str(risk_level):
        fallback = [
            {"name": "Nearest Government District Hospital", "address": "", "maps_url": "", "lat": None, "lng": None},
            {"name": "Call 108 for emergency ambulance", "address": "", "maps_url": "", "lat": None, "lng": None}
        ]
    elif "Medium" in str(risk_level):
        fallback = [
            {"name": "Primary Health Center (PHC)", "address": "", "maps_url": "", "lat": None, "lng": None},
            {"name": "Community Health Center", "address": "", "maps_url": "", "lat": None, "lng": None}
        ]
    else:
        fallback = [
            {"name": "Monitor symptoms at home", "address": "", "maps_url": ""},
            {"name": "Consult local healthcare provider if symptoms worsen", "address": "", "maps_url": ""}
        ]

    _cache_set(key_for_cache, fallback)
    return fallback

def get_embed_map_url(location_query):
    """Return Google embed url if key present else empty string (app will fallback to OSM embed)."""
    if not MAPS_EMBED_KEY:
        return ""
    try:
        q = requests.utils.quote(location_query)
        return f"https://www.google.com/maps/embed/v1/place?key={MAPS_EMBED_KEY}&q={q}"
    except Exception:
        return ""
