#!/usr/bin/env python3
"""
Get ALL dramas from hotRank (correct structure)
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

# Get hotRank
result = api_request("/app/playlet/hotRank")

all_ids = set()

if result.get('status_code') == 1:
    categories = result.get('data', [])
    
    print(f"{'='*60}")
    print("HOTRANK CATEGORIES:")
    print("="*60)
    
    for cat in categories:
        cat_name = cat.get('name', 'Unknown')
        cat_data = cat.get('data', [])  # Using 'data' not 'list'
        print(f"\n{cat_name}: {len(cat_data)} dramas")
        
        for drama in cat_data[:10]:
            drama_id = drama.get('playlet_id')
            title = drama.get('title', 'N/A')[:40]
            all_ids.add(str(drama_id))
            print(f"  {drama_id}: {title}")
        
        if len(cat_data) > 10:
            print(f"  ... and {len(cat_data) - 10} more")
        
        # Add all to set
        for drama in cat_data:
            all_ids.add(str(drama.get('playlet_id')))

print(f"\n{'='*60}")
print(f"Total unique dramas in hotRank: {len(all_ids)}")
print("="*60)
