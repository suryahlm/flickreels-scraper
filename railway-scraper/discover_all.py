#!/usr/bin/env python3
"""
Comprehensive Indonesian Drama Discovery
Explore all navigation tabs and collect all unique dramas
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

def get_navigation():
    """Get all navigation tabs"""
    result = api_request("/app/playlet/navigation")
    if result.get('status_code') == 1:
        return result.get('data', [])
    return []

def get_dramas_lastcolumn(page, navigation_id, column_config_id):
    """Get dramas from lastColumn endpoint"""
    result = api_request("/app/playlet/lastColumn", {
        "page": page,
        "page_size": 50,
        "navigation_id": str(navigation_id),
        "column_config_id": str(column_config_id)
    })
    
    if result.get('status_code') == 1:
        data = result.get('data')
        if data and isinstance(data, dict):
            return data.get('list', [])
    return []

def get_dramas_navcolumn(navigation_id, page=1):
    """Get dramas from navigationColumn endpoint"""
    result = api_request("/app/playlet/navigationColumn", {
        "page": page,
        "page_size": 50,
        "navigation_id": str(navigation_id)
    })
    
    if result.get('status_code') == 1:
        data = result.get('data', [])
        if not data:
            return []
        all_items = []
        for section in data:
            if isinstance(section, dict) and 'list' in section:
                all_items.extend(section['list'])
        return all_items
    return []


print("="*70)
print("COMPREHENSIVE INDONESIAN DRAMA DISCOVERY")
print("="*70)

# Get navigation
navs = get_navigation()
print(f"Found {len(navs)} navigation tabs:")
for nav in navs:
    print(f"  {nav.get('id')}: {nav.get('name')}")

# Collect all unique dramas
all_dramas = {}
discovery_sources = {}

# Method 1: Explore each navigation with navigationColumn
print("\n" + "="*70)
print("Method 1: navigationColumn for each navigation tab")
print("="*70)

for nav in navs:
    nav_id = nav.get('id')
    nav_name = nav.get('name', 'Unknown')
    
    print(f"\nExploring navigation {nav_id}: {nav_name}")
    
    for page in range(1, 20):  # Up to 20 pages per nav
        items = get_dramas_navcolumn(nav_id, page)
        
        if not items:
            break
        
        new_count = 0
        for item in items:
            drama_id = str(item.get('playlet_id'))
            if drama_id and drama_id not in all_dramas:
                all_dramas[drama_id] = {
                    'id': item.get('playlet_id'),
                    'title': item.get('title'),
                    'cover': item.get('cover'),
                    'episodes': item.get('upload_num', 0)
                }
                discovery_sources[drama_id] = f"nav_{nav_id}_page_{page}"
                new_count += 1
        
        print(f"  Page {page}: {len(items)} items, {new_count} new. Total: {len(all_dramas)}")
        
        if new_count == 0:
            break
        
        time.sleep(0.2)

# Method 2: Use lastColumn with column_config_id
print("\n" + "="*70)
print("Method 2: lastColumn with column_config_id=11274")
print("="*70)

for page in range(1, 100):  # Up to 100 pages
    items = get_dramas_lastcolumn(page, 30, 11274)
    
    if not items:
        print(f"  Page {page}: empty - stopping")
        break
    
    new_count = 0
    for item in items:
        drama_id = str(item.get('playlet_id'))
        if drama_id and drama_id not in all_dramas:
            all_dramas[drama_id] = {
                'id': item.get('playlet_id'),
                'title': item.get('title'),
                'cover': item.get('cover'),
                'episodes': item.get('upload_num', 0)
            }
            discovery_sources[drama_id] = f"lastColumn_page_{page}"
            new_count += 1
    
    print(f"  Page {page}: {len(items)} items, {new_count} new. Total: {len(all_dramas)}")
    
    if new_count == 0 and page > 5:
        print("  No new items for multiple pages - stopping")
        break
    
    time.sleep(0.2)

# Summary
print("\n" + "="*70)
print(f"TOTAL UNIQUE INDONESIAN DRAMAS: {len(all_dramas)}")
print("="*70)

# Save to file
dramas_list = list(all_dramas.values())
with open("discovered_indonesia_comprehensive.json", "w", encoding="utf-8") as f:
    json.dump(dramas_list, f, ensure_ascii=False, indent=2)
print(f"Saved to discovered_indonesia_comprehensive.json")

# Show sample
print("\nSample titles:")
for drama in dramas_list[:15]:
    print(f"  {drama['id']}: {drama['title'][:50]}")
