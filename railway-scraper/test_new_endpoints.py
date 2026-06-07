#!/usr/bin/env python3
"""
Test new endpoints found from HAR
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from batch_scraper_indonesia import generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY

def api_request(endpoint, extra_body=None):
    body = {**INDONESIAN_BODY, **(extra_body or {})}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    
    headers = {
        "token": FLICKREELS_CONFIG["token"],
        "sign": sign,
        "timestamp": timestamp,
        "nonce": nonce,
        "version": FLICKREELS_CONFIG["version"],
        "content-type": "application/json"
    }
    
    resp = requests.post(
        f"{FLICKREELS_CONFIG['base_url']}{endpoint}",
        json=body,
        headers=headers,
        timeout=15
    )
    return resp.json()

endpoints_to_test = [
    ("/app/playlet/forYou", {}),
    ("/app/playlet/forYou", {"page": 1, "page_size": 50}),
    ("/app/playlet/hotRank", {}),
    ("/app/playlet/hotRank", {"page": 1, "page_size": 50}),
    ("/app/playlet/latestPlay", {}),
    ("/app/playlet/latestPlay", {"page": 1, "page_size": 50}),
    ("/app/user_search/searchRankList", {}),
]

all_ids = set()

for endpoint, extra in endpoints_to_test:
    print(f"\n{endpoint}")
    if extra:
        print(f"  Body: {extra}")
    
    result = api_request(endpoint, extra)
    status = result.get('status_code')
    msg = result.get('msg', '')
    
    if status == 1:
        data = result.get('data')
        
        if isinstance(data, list):
            print(f"  SUCCESS: list with {len(data)} items")
            for item in data:
                if isinstance(item, dict):
                    drama_id = item.get('playlet_id') or item.get('id')
                    if drama_id:
                        all_ids.add(str(drama_id))
                    title = item.get('title', item.get('name', 'N/A'))[:40]
                    print(f"    ID {drama_id}: {title}")
        elif isinstance(data, dict):
            items = data.get('list', [])
            print(f"  SUCCESS: dict with list of {len(items)} items")
            for item in items[:5]:
                drama_id = item.get('playlet_id') or item.get('id')
                if drama_id:
                    all_ids.add(str(drama_id))
                title = item.get('title', 'N/A')[:40]
                print(f"    ID {drama_id}: {title}")
        else:
            print(f"  Data type: {type(data)}")
    else:
        print(f"  FAILED: {msg}")
    
    time.sleep(0.3)

print(f"\n{'='*60}")
print(f"Total unique IDs found from these endpoints: {len(all_ids)}")
