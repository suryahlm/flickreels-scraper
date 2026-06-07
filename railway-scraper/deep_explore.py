#!/usr/bin/env python3
"""
Explore ALL navigation tabs and their columns deeply
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
        return {"status_code": -1, "msg": str(e)}

# Get navigation tabs
print("="*70)
print("EXPLORING ALL NAVIGATION TABS")
print("="*70)

nav_result = api_request("/app/playlet/navigation")
if nav_result.get('status_code') != 1:
    print("Failed to get navigation!")
    exit(1)

navs = nav_result.get('data', [])
print(f"Found {len(navs)} navigation tabs:\n")

all_dramas = {}

for nav in navs:
    nav_id = nav.get('id')
    nav_name = nav.get('name')
    columns = nav.get('list', [])
    
    print(f"\n{'='*70}")
    print(f"Tab: {nav_name} (nav_id={nav_id})")
    print(f"  Has {len(columns)} columns")
    print("="*70)
    
    # Show columns
    for col in columns:
        col_id = col.get('id')
        col_name = col.get('name')
        col_type = col.get('type')
        print(f"  Column {col_id}: '{col_name}' (type={col_type})")
    
    # Try to get dramas from each column
    for col in columns:
        col_id = col.get('id')
        col_name = col.get('name')
        
        # Try lastColumn endpoint
        result = api_request("/app/playlet/lastColumn", {
            "navigation_id": str(nav_id),
            "column_config_id": str(col_id),
            "page": 1,
            "page_size": 50
        })
        
        if result.get('status_code') == 1:
            data = result.get('data')
            if data and isinstance(data, dict):
                items = data.get('list', [])
                if items:
                    new_count = 0
                    for item in items:
                        drama_id = str(item.get('playlet_id'))
                        if drama_id not in all_dramas:
                            all_dramas[drama_id] = {
                                'id': drama_id,
                                'title': item.get('title'),
                                'cover': item.get('cover'),
                                'source': f'{nav_name}/{col_name}'
                            }
                            new_count += 1
                    print(f"    -> lastColumn: {len(items)} items, {new_count} NEW")
        
        time.sleep(0.2)
    
    # Also try navigationColumn
    result = api_request("/app/playlet/navigationColumn", {
        "navigation_id": str(nav_id),
        "page": 1,
        "page_size": 50
    })
    
    if result.get('status_code') == 1:
        data = result.get('data', [])
        if data:
            total = 0
            new_total = 0
            for section in data:
                if isinstance(section, dict):
                    items = section.get('list', [])
                    total += len(items)
                    for item in items:
                        drama_id = str(item.get('playlet_id'))
                        if drama_id not in all_dramas:
                            all_dramas[drama_id] = {
                                'id': drama_id,
                                'title': item.get('title'),
                                'cover': item.get('cover'),
                                'source': f'{nav_name}/navColumn'
                            }
                            new_total += 1
            print(f"  -> navigationColumn page 1: {total} items, {new_total} NEW")
    
    time.sleep(0.3)

print(f"\n{'='*70}")
print(f"TOTAL UNIQUE DRAMAS FOUND: {len(all_dramas)}")
print("="*70)

# Save
with open("deep_discovery.json", "w", encoding="utf-8") as f:
    json.dump(list(all_dramas.values()), f, ensure_ascii=False, indent=2)
print("Saved to deep_discovery.json")

# Show sources breakdown
sources = {}
for d in all_dramas.values():
    src = d.get('source', 'unknown')
    sources[src] = sources.get(src, 0) + 1

print("\nBreakdown by source:")
for src, count in sorted(sources.items(), key=lambda x: -x[1]):
    print(f"  {src}: {count}")
