#!/usr/bin/env python3
"""
Count total Indonesian dramas via lastColumn endpoint - Fixed version
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from batch_scraper_indonesia import generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY

def get_dramas_page(page, column_config_id="11274", navigation_id="30"):
    """Get dramas from a page"""
    
    body = {
        **INDONESIAN_BODY,
        "page": page,
        "page_size": 50,
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
        print(f"  Error on page {page}: {e}")
        return []

print("Counting total Indonesian dramas...")
print("=" * 60)

all_dramas = []
all_ids = set()
page = 1
empty_count = 0

while empty_count < 5:  # Stop after 5 consecutive empty/duplicate pages
    items = get_dramas_page(page)
    
    if not items:
        empty_count += 1
        print(f"Page {page}: empty ({empty_count}/5)")
    else:
        new_items = [item for item in items if str(item.get('playlet_id')) not in all_ids]
        
        if len(new_items) == 0:
            empty_count += 1
            print(f"Page {page}: no new items ({empty_count}/5)")
        else:
            empty_count = 0
            for item in new_items:
                all_ids.add(str(item.get('playlet_id')))
                all_dramas.append({
                    'id': item.get('playlet_id'),
                    'title': item.get('title'),
                    'cover': item.get('cover'),
                    'episodes': item.get('upload_num', 0)
                })
            
            print(f"Page {page}: {len(items)} items, {len(new_items)} new. Total: {len(all_ids)}")
    
    page += 1
    time.sleep(0.3)
    
    if page > 500:  # Safety limit
        print("Reached page limit")
        break

print(f"\n{'='*60}")
print(f"TOTAL UNIQUE INDONESIAN DRAMAS: {len(all_dramas)}")
print(f"{'='*60}")

# Save to file
with open("discovered_indonesia_new.json", "w", encoding="utf-8") as f:
    json.dump(all_dramas, f, ensure_ascii=False, indent=2)
print(f"Saved to discovered_indonesia_new.json")

# Show some sample titles
print("\nSample titles:")
for drama in all_dramas[:10]:
    print(f"  {drama['id']}: {drama['title'][:50]}")
