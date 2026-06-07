#!/usr/bin/env python3
"""Fix cover images for drama 1675 and 5247"""
import requests
import boto3
from botocore.config import Config
import json
import time
import hashlib
import hmac
import random
import string

# Config
R2_CONFIG = {
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com",
    "access_key_id": "a4903ea93c248388b6e295d6cdbc8617",
    "secret_access_key": "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9",
    "bucket_name": "asiandrama-cdn"
}

SUPABASE_URL = "https://bmryonqbddbkjbtquhgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"

FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU",
    "version": "2.2.3.0"
}

BODY_PARAMS = {
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
    body_json = json.dumps(body, separators=(',', ':'))
    str_d = method_d(body_json)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    return hmac.new(
        FLICKREELS_CONFIG["secret_key"].encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def get_drama_cover(drama_id):
    """Get cover URL from FlickReels API"""
    body = {**BODY_PARAMS, "playlet_id": str(drama_id)}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    
    headers = {
        "version": FLICKREELS_CONFIG["version"],
        "user-agent": "MyUserAgent",
        "content-type": "application/json; charset=UTF-8",
        "token": FLICKREELS_CONFIG["token"],
        "sign": sign,
        "timestamp": timestamp,
        "nonce": nonce
    }
    
    url = f"{FLICKREELS_CONFIG['base_url']}/app/playlet/chapterList"
    response = requests.post(url, json=body, headers=headers, timeout=30)
    data = response.json()
    
    if data.get("status_code") == 1:
        return data.get("data", {}).get("cover")
    return None

def fix_drama_cover(drama_id, r2_folder):
    """Download actual cover and upload to R2, then update Supabase"""
    print(f"\nFixing cover for drama {drama_id}...")
    
    # Get actual cover URL from API
    cover_url = get_drama_cover(drama_id)
    if not cover_url:
        print(f"  ERROR: Could not get cover from API")
        return False
    
    print(f"  Cover URL: {cover_url[:80]}...")
    
    # Download cover
    cover_response = requests.get(cover_url, timeout=30)
    if cover_response.status_code != 200:
        print(f"  ERROR: Failed to download cover")
        return False
    
    # Upload to R2
    r2 = boto3.client('s3',
        endpoint_url=R2_CONFIG["endpoint_url"],
        aws_access_key_id=R2_CONFIG["access_key_id"],
        aws_secret_access_key=R2_CONFIG["secret_access_key"],
        config=Config(signature_version='s3v4')
    )
    
    r2_key = f"flickreels/{r2_folder}/cover.jpg"
    r2.put_object(
        Bucket=R2_CONFIG["bucket_name"],
        Key=r2_key,
        Body=cover_response.content,
        ContentType="image/jpeg"
    )
    print(f"  Uploaded to R2: {r2_key}")
    
    # Update Supabase thumbnail_url
    stream_base = "https://tender-connection-production-246f.up.railway.app/api/stream"
    new_thumbnail = f"{stream_base}/{r2_key}"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{drama_id}",
        headers=headers,
        json={"thumbnail_url": new_thumbnail}
    )
    
    if resp.status_code in [200, 204]:
        print(f"  Updated Supabase thumbnail_url: {new_thumbnail}")
        return True
    else:
        print(f"  ERROR: Supabase update failed: {resp.status_code}")
        return False

# Fix both dramas
dramas = [
    {"id": "1675", "folder": "CEO itu Ayah Anakku (1675)"},
    {"id": "5247", "folder": "Peramal Wanita (5247)"}
]

for drama in dramas:
    fix_drama_cover(drama["id"], drama["folder"])

print("\nDone!")
