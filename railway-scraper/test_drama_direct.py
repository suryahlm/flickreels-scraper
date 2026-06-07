#!/usr/bin/env python3
"""Test getting drama details directly from known IDs"""
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

# Test beberapa ID dari new_dramas_list.txt
test_ids = [376, 391, 421, 426, 457, 489, 492, 495, 499, 658]

print("Testing drama detail API with known Indonesian IDs...")
print("=" * 60)

success = 0
failed = 0

for drama_id in test_ids:
    body = {
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
        "countryCode": "ID",
        "playlet_id": str(drama_id)
    }
    
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
        response = requests.post("https://api.farsunpteltd.com/app/playlet/chapterList", 
                                json=body, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("status_code") == 1:
            d = data.get("data", {})
            title = d.get("title", "N/A")
            eps = len(d.get("list", []))
            print(f"✅ ID {drama_id}: {title} - {eps} episodes")
            success += 1
        else:
            msg = data.get("msg", "Unknown error")
            print(f"❌ ID {drama_id}: FAILED - {msg}")
            failed += 1
    except Exception as e:
        print(f"❌ ID {drama_id}: ERROR - {e}")
        failed += 1
    
    time.sleep(0.3)

print("=" * 60)
print(f"Results: {success} success, {failed} failed")
