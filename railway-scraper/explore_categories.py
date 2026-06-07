#!/usr/bin/env python3
"""
Try to find category/genre endpoints for more dramas
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from batch_scraper_indonesia import generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY

def api_request(endpoint, extra_body=None):
    """Generic API request"""
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
    
    try:
        resp = requests.post(
            f"{FLICKREELS_CONFIG['base_url']}{endpoint}",
            json=body,
            headers=headers,
            timeout=15
        )
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return {"status_code": -1, "msg": str(e)}

print("="*70)
print("EXPLORING CATEGORY/GENRE/TAG ENDPOINTS")
print("="*70)

# Try various endpoints that might have category lists
endpoints_to_try = [
    ("/app/playlet/categoryList", {}),
    ("/app/playlet/tagList", {}),
    ("/app/playlet/genreList", {}),
    ("/app/playlet/classify", {}),
    ("/app/playlet/category", {}),
    ("/app/playlet/hot", {}),
    ("/app/playlet/recommend", {}),
    ("/app/playlet/rankingList", {"type": 1}),
    ("/app/playlet/rankingList", {"type": 2}),
    ("/app/playlet/collect", {}),  # Maybe collected/favorites
    ("/app/playlet/history", {}),  # Watch history
]

for endpoint, extra in endpoints_to_try:
    result = api_request(endpoint, extra)
    
    status = result.get('status_code')
    msg = result.get('msg', '')
    
    print(f"\n{endpoint}")
    if extra:
        print(f"  Body: {extra}")
    print(f"  Status: {status}, Message: {msg}")
    
    if status == 1:
        data = result.get('data')
        if isinstance(data, list):
            print(f"  Data: list with {len(data)} items")
            if data and isinstance(data[0], dict):
                print(f"    First item keys: {list(data[0].keys())[:8]}")
                if 'id' in data[0] or 'playlet_id' in data[0]:
                    ids = [d.get('id') or d.get('playlet_id') for d in data[:5]]
                    print(f"    First 5 IDs: {ids}")
        elif isinstance(data, dict):
            print(f"  Data: dict with keys: {list(data.keys())[:10]}")
    
    time.sleep(0.3)

# Now try search with empty query - might return all
print("\n" + "="*70)
print("TRYING SEARCH ENDPOINT")
print("="*70)

for query in ["", "cinta", "mafia", "bosses"]:
    result = api_request("/app/playlet/search", {"keyword": query, "page": 1, "page_size": 50})
    
    status = result.get('status_code')
    if status == 1:
        data = result.get('data', {})
        if isinstance(data, dict):
            items = data.get('list', [])
            total = data.get('total', 'unknown')
            print(f"\nSearch '{query}': {len(items)} items returned, total reported: {total}")
            if items:
                print(f"  Sample titles: {[i.get('title')[:30] for i in items[:3]]}")
        elif isinstance(data, list):
            print(f"\nSearch '{query}': {len(data)} items")
    else:
        print(f"\nSearch '{query}': status={status}, msg={result.get('msg')}")
    
    time.sleep(0.3)
