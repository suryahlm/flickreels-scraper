#!/usr/bin/env python3
"""
COMPREHENSIVE: Collect from ALL known endpoints
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

all_dramas = {}

def add_drama(item, source):
    drama_id = str(item.get('playlet_id') or item.get('id', ''))
    if drama_id and drama_id != 'None':
        if drama_id not in all_dramas:
            all_dramas[drama_id] = {
                'id': drama_id,
                'title': item.get('title', ''),
                'cover': item.get('cover', ''),
                'source': source
            }

print("="*70)
print("COMPREHENSIVE DRAMA COLLECTION")
print("="*70)

# 1. navigationColumn for all nav_ids
nav_ids = [30, 78, 387, 454, 88]
for nav_id in nav_ids:
    for page in range(1, 20):
        result = api_request("/app/playlet/navigationColumn", {
            "navigation_id": str(nav_id),
            "page": page,
            "page_size": 50
        })
        if result.get('status_code') != 1:
            break
        
        data = result.get('data', [])
        if not data:
            break
        
        count = 0
        for section in data:
            if isinstance(section, dict):
                for item in section.get('list', []):
                    add_drama(item, f"navColumn_{nav_id}")
                    count += 1
        
        if count == 0:
            break
    
    print(f"After navColumn nav={nav_id}: {len(all_dramas)} total")
    time.sleep(0.2)

# 2. lastColumn for known configs
configs = [("30", "11274"), ("78", "6826")]
for nav_id, config_id in configs:
    for page in range(1, 50):
        result = api_request("/app/playlet/lastColumn", {
            "navigation_id": nav_id,
            "column_config_id": config_id,
            "page": page,
            "page_size": 50
        })
        
        if result.get('status_code') != 1:
            break
        
        data = result.get('data')
        if not data or not isinstance(data, dict):
            break
        
        items = data.get('list', [])
        if not items:
            break
        
        for item in items:
            add_drama(item, f"lastColumn_{config_id}")
    
    print(f"After lastColumn config={config_id}: {len(all_dramas)} total")
    time.sleep(0.2)

# 3. hotRank
result = api_request("/app/playlet/hotRank")
if result.get('status_code') == 1:
    for cat in result.get('data', []):
        for item in cat.get('data', []):
            add_drama(item, "hotRank")
print(f"After hotRank: {len(all_dramas)} total")

# 4. forYou
result = api_request("/app/playlet/forYou")
if result.get('status_code') == 1:
    data = result.get('data', {})
    items = data.get('list', []) if isinstance(data, dict) else data
    for item in items:
        add_drama(item, "forYou")
print(f"After forYou: {len(all_dramas)} total")

# 5. searchRankList
result = api_request("/app/user_search/searchRankList")
if result.get('status_code') == 1:
    for item in result.get('data', []):
        add_drama(item, "searchRank")
print(f"After searchRank: {len(all_dramas)} total")

print(f"\n{'='*70}")
print(f"TOTAL UNIQUE DRAMAS: {len(all_dramas)}")
print("="*70)

# Save
with open("comprehensive_dramas.json", "w", encoding="utf-8") as f:
    json.dump(list(all_dramas.values()), f, ensure_ascii=False, indent=2)
print(f"Saved to comprehensive_dramas.json")

# Source breakdown
sources = {}
for d in all_dramas.values():
    src = d.get('source', 'unknown')
    sources[src] = sources.get(src, 0) + 1
print("\nBy source:")
for src, count in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {src}: {count}")
