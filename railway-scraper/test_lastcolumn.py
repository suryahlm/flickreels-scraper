#!/usr/bin/env python3
"""
Test /app/playlet/lastColumn endpoint for pagination
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from batch_scraper_indonesia import generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY

def test_last_column(page=1, column_config_id="11274", navigation_id="30"):
    """Test the lastColumn endpoint"""
    
    body = {
        **INDONESIAN_BODY,
        "page": page,
        "page_size": 20,
        "navigation_id": navigation_id,
        "column_config_id": column_config_id
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
    
    resp = requests.post(
        f"{FLICKREELS_CONFIG['base_url']}/app/playlet/lastColumn",
        json=body,
        headers=headers,
        timeout=15
    )
    
    return resp.json()

# Test pagination
print("Testing /app/playlet/lastColumn with column_config_id=11274")
print("=" * 60)

all_ids = set()
for page in range(1, 11):  # Test 10 pages
    result = test_last_column(page=page)
    
    if result.get('status_code') == 1:
        data = result.get('data', {})
        items = data.get('list', [])
        
        page_ids = [str(item.get('playlet_id')) for item in items]
        new_ids = set(page_ids) - all_ids
        all_ids.update(page_ids)
        
        if items:
            first_title = items[0].get('title', 'N/A')[:40]
            print(f"Page {page}: {len(items)} items, {len(new_ids)} new (e.g. \"{first_title}\")")
        else:
            print(f"Page {page}: 0 items (end of list)")
            break
    else:
        print(f"Page {page}: Error - {result.get('msg', 'Unknown')}")
        break
    
    time.sleep(0.3)

print(f"\nTotal unique dramas: {len(all_ids)}")
