#!/usr/bin/env python3
"""Check for NEW Indonesian dramas not yet in database"""
import requests
import json
import time
import hashlib
import hmac
import random
import string

def generate_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def method_d(body_json):
    if not body_json or body_json == "{}":
        return ""
    data = json.loads(body_json)
    sorted_data = dict(sorted(data.items()))
    parts = []
    for key, value in sorted_data.items():
        if value is not None:
            if isinstance(value, bool):
                value_str = 'true' if value else 'false'
            elif isinstance(value, (list, dict)):
                value_str = json.dumps(value, separators=(',', ':'))
            else:
                value_str = str(value)
            parts.append(f'{key}_{value_str}')
    return '_'.join(parts)

def generate_sign(body, timestamp, nonce):
    secret_key = "tsM5SnqFayhX7c2HfRxm"
    body_json = json.dumps(body, separators=(',', ':'))
    str_d = method_d(body_json)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    return hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"

base_body = {
    "main_package_id": 100,
    "googleAdId": "783978b6-0d30-438d-a58d-faf171eed978",
    "device_id": "0d209b4d4009b44c",
    "device_sign": "0ee806655facff8960c6e146fe984fadb52b0cb794cea9a0ed2030d08a179215",
    "apps_flyer_uid": "1769621528308-5741215934785896746",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "language_id": "6",
    "countryCode": "ID"
}

# Load existing IDs from Supabase
print("Loading existing drama IDs from Supabase...")
existing_ids = set()
resp = requests.get(
    "https://bmryonqbddbkjbtquhgu.supabase.co/rest/v1/dramas?select=flickreels_id",
    headers={"apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"}
)
if resp.status_code == 200:
    for d in resp.json():
        if d.get("flickreels_id"):
            existing_ids.add(str(d["flickreels_id"]))
print(f"Existing in DB: {len(existing_ids)}")

# Check lastColumn for NEW dramas
print("\nChecking lastColumn (Baru/New) for fresh content...")
new_dramas = []

# Multiple endpoints to check
endpoints = [
    ("78", "6826", "Baru/New"),      # New releases
    ("30", "11274", "Home"),          # Home page
    ("387", None, "Romance"),         # Romance category
    ("88", None, "Drama"),            # Drama category
]

for nav_id, config_id, name in endpoints:
    print(f"\nChecking {name} (nav={nav_id})...")
    
    for page in range(1, 20):  # Check 20 pages
        body = {**base_body, "navigation_id": nav_id, "page": page, "page_size": 50}
        if config_id:
            body["column_config_id"] = config_id
            endpoint = "/app/playlet/lastColumn"
        else:
            endpoint = "/app/playlet/navigationColumn"
        
        timestamp = str(int(time.time()))
        nonce = generate_nonce()
        sign = generate_sign(body, timestamp, nonce)
        headers = {
            "version": "2.2.3.0", 
            "user-agent": "MyUserAgent", 
            "content-type": "application/json; charset=UTF-8", 
            "token": token, 
            "sign": sign, 
            "timestamp": timestamp, 
            "nonce": nonce
        }
        
        try:
            response = requests.post(f"https://api.farsunpteltd.com{endpoint}", json=body, headers=headers, timeout=30)
            data = response.json()
            
            items = []
            if data.get("status_code") == 1:
                if config_id and data.get("data", {}).get("list"):
                    items = data["data"]["list"]
                elif not config_id and data.get("data"):
                    for section in data["data"]:
                        items.extend(section.get("list", []))
            
            new_count = 0
            for item in items:
                drama_id = str(item.get("playlet_id"))
                if drama_id not in existing_ids:
                    new_dramas.append({
                        "id": drama_id, 
                        "title": item.get("title"),
                        "cover": item.get("cover"),
                        "source": name
                    })
                    existing_ids.add(drama_id)  # Don't count duplicates
                    new_count += 1
            
            if new_count > 0:
                print(f"  Page {page}: {new_count} new found")
            
            if not items:
                break  # No more pages
                
            time.sleep(0.3)
        except Exception as e:
            print(f"  Error page {page}: {e}")
            break

# Print results
print("\n" + "=" * 60)
print(f"NEW dramas found (not in DB): {len(new_dramas)}")
print("=" * 60)

if new_dramas:
    print("\nTop 20 new dramas:")
    for i, d in enumerate(new_dramas[:20], 1):
        title = d["title"][:35] if d.get("title") else "N/A"
        print(f"  {i:2d}. [{d['id']:>5}] {title}")
    
    # Save to file
    with open("newly_discovered.json", "w", encoding="utf-8") as f:
        json.dump(new_dramas, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(new_dramas)} dramas to newly_discovered.json")
else:
    print("\nNo NEW dramas found - database is up to date!")
