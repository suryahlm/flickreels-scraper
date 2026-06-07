#!/usr/bin/env python3
"""
Explore different column_config_ids to find more Indonesian dramas
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from batch_scraper_indonesia import generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY

def get_column_configs():
    """Get available column configs from navigation endpoint"""
    
    body = {**INDONESIAN_BODY}
    
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
        f"{FLICKREELS_CONFIG['base_url']}/app/playlet/navigation",
        json=body,
        headers=headers,
        timeout=15
    )
    
    return resp.json()

def get_dramas_page(page, column_config_id, navigation_id="30"):
    """Get dramas from a page"""
    
    body = {
        **INDONESIAN_BODY,
        "page": page,
        "page_size": 50,
        "navigation_id": navigation_id,
        "column_config_id": str(column_config_id)
    }
    
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
            f"{FLICKREELS_CONFIG['base_url']}/app/playlet/lastColumn",
            json=body,
            headers=headers,
            timeout=15
        )
        
        result = resp.json()
        if result.get('status_code') == 1:
            data = result.get('data')
            if data and isinstance(data, dict):
                return data.get('list', [])
        return []
    except Exception as e:
        return []

# First, get navigation info
print("Getting navigation info...")
nav_result = get_column_configs()
print(f"Status: {nav_result.get('status_code')}")

if nav_result.get('status_code') == 1:
    nav_data = nav_result.get('data', [])
    print(f"Found {len(nav_data)} navigation tabs\n")
    
    for nav in nav_data:
        print(f"Navigation ID: {nav.get('id')} - {nav.get('name')}")
        columns = nav.get('list', [])
        for col in columns[:5]:  # First 5 columns
            print(f"  Column {col.get('id')}: {col.get('name')}")

# Now explore known column_config_ids
print("\n" + "="*60)
print("Exploring column_config_ids for Indonesian dramas...")
print("="*60)

# Try various column_config_ids
config_ids = [11274, 6826, 11275, 11276, 11277, 11278, 11279, 11280]
all_ids = set()

for config_id in config_ids:
    items = get_dramas_page(1, config_id)
    if items:
        new_items = [item for item in items if str(item.get('playlet_id')) not in all_ids]
        for item in new_items:
            all_ids.add(str(item.get('playlet_id')))
        
        first_title = items[0].get('title', 'N/A')[:40] if items else 'N/A'
        print(f"Column {config_id}: {len(items)} items, {len(new_items)} new (e.g. \"{first_title}\")")
    else:
        print(f"Column {config_id}: empty or error")
    
    time.sleep(0.3)

print(f"\nTotal unique from tested columns: {len(all_ids)}")
