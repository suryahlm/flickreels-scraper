#!/usr/bin/env python3
"""
Discover Indonesian dramas BEYOND the 495 limit.
Strategy:
  1. Probe user_search endpoint for search capability
  2. Try navigationColumn with different nav_ids
  3. Try forYou / lastColumn endpoints
  4. Vowel brute-force search (a, i, u, e, o)
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from local_scraping_indonesia import IndonesianAPI, generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY, SUPABASE_CONFIG

api = IndonesianAPI()

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
        print(f"  Error: {e}")
        return {"status_code": -1, "msg": str(e)}

# Load existing IDs from Supabase
print("Loading existing drama IDs from Supabase...")
resp = requests.get(
    f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
    headers={"apikey": SUPABASE_CONFIG["key"]}
)
existing_ids = set()
if resp.status_code == 200:
    for d in resp.json():
        if d.get('flickreels_id'):
            existing_ids.add(str(d['flickreels_id']))
print(f"  Found {len(existing_ids)} existing dramas\n")

all_found = {}  # id -> title

# ============================================================
# PROBE 1: user_search endpoints
# ============================================================
print("=" * 70)
print("PROBE 1: user_search endpoints")
print("=" * 70)

# Get hot keywords first
result = api_request("/app/user_search/getHotKeywordList")
print(f"\ngetHotKeywordList: status={result.get('status_code')}")
if result.get('status_code') == 1:
    data = result.get('data', [])
    if isinstance(data, list):
        print(f"  Hot keywords: {[d.get('keyword', d) if isinstance(d, dict) else d for d in data[:10]]}")

# Search rank 
result = api_request("/app/user_search/searchRankList")
print(f"\nsearchRankList: status={result.get('status_code')}")
if result.get('status_code') == 1:
    data = result.get('data', [])
    if isinstance(data, list):
        print(f"  Rank items: {len(data)}")
        for d in data[:5]:
            print(f"    - {d.get('title', d)}")

# Try search endpoint variations
search_endpoints = [
    "/app/user_search/search",
    "/app/user_search/searchPlaylet", 
    "/app/user_search/querySearch",
    "/app/playlet/searchPlaylet",
    "/app/search/playlet",
    "/app/search/index",
]

for ep in search_endpoints:
    result = api_request(ep, {"keyword": "cinta", "page": 1, "page_size": 50})
    status = result.get('status_code')
    msg = result.get('msg', '')
    
    if status == 1:
        data = result.get('data', {})
        if isinstance(data, dict):
            items = data.get('list', [])
            total = data.get('total', len(items))
            print(f"\n✅ FOUND SEARCH: {ep}")
            print(f"  Results: {len(items)}, Total: {total}")
            if items:
                for item in items[:3]:
                    pid = str(item.get('playlet_id', item.get('id', '')))
                    title = item.get('title', '')
                    print(f"    - [{pid}] {title}")
        elif isinstance(data, list):
            print(f"\n✅ FOUND SEARCH: {ep}")
            print(f"  Results: {len(data)}")
    else:
        print(f"\n❌ {ep}: {msg[:50]}")
    
    time.sleep(0.3)

# ============================================================
# PROBE 2: navigationColumn with DIFFERENT nav_ids
# ============================================================
print("\n" + "=" * 70)
print("PROBE 2: navigationColumn with different nav_ids")
print("=" * 70)

# Try nav_ids beyond 30 (which is the standard Indonesian feed)
for nav_id in range(1, 50):
    result = api_request("/app/playlet/navigationColumn", {
        "navigation_id": str(nav_id),
        "page": 1,
        "page_size": 50
    })
    
    if result.get('status_code') == 1:
        data = result.get('data', [])
        total_items = 0
        new_items = 0
        sample_titles = []
        
        if isinstance(data, list):
            for section in data:
                items = section.get('list', [])
                total_items += len(items)
                for item in items:
                    pid = str(item.get('playlet_id', ''))
                    title = item.get('title', '')
                    if pid and pid not in existing_ids:
                        new_items += 1
                        all_found[pid] = title
                    if title and len(sample_titles) < 2:
                        sample_titles.append(title[:30])
        
        if total_items > 0:
            print(f"  nav_id={nav_id}: {total_items} items, {new_items} NEW | {sample_titles}")
    
    time.sleep(0.2)

# ============================================================
# PROBE 3: forYou and lastColumn
# ============================================================
print("\n" + "=" * 70)
print("PROBE 3: forYou and lastColumn")
print("=" * 70)

for page in range(1, 6):
    result = api_request("/app/playlet/forYou", {"page": page, "page_size": 50})
    if result.get('status_code') == 1:
        data = result.get('data', {})
        if isinstance(data, dict):
            items = data.get('list', [])
            new = 0
            for item in items:
                pid = str(item.get('playlet_id', ''))
                if pid and pid not in existing_ids:
                    new += 1
                    all_found[pid] = item.get('title', '')
            print(f"  forYou page {page}: {len(items)} items, {new} NEW")
        else:
            print(f"  forYou page {page}: data type = {type(data).__name__}")
    else:
        print(f"  forYou page {page}: {result.get('msg', 'error')[:50]}")
        break
    time.sleep(0.3)

for page in range(1, 6):
    result = api_request("/app/playlet/lastColumn", {"page": page, "page_size": 50})
    if result.get('status_code') == 1:
        data = result.get('data', [])
        new = 0
        total = 0
        if isinstance(data, list):
            for section in data:
                items = section.get('list', [])
                total += len(items)
                for item in items:
                    pid = str(item.get('playlet_id', ''))
                    if pid and pid not in existing_ids:
                        new += 1
                        all_found[pid] = item.get('title', '')
        print(f"  lastColumn page {page}: {total} items, {new} NEW")
    else:
        print(f"  lastColumn page {page}: {result.get('msg', 'error')[:50]}")
        break
    time.sleep(0.3)

# ============================================================
# PROBE 4: Vowel Search (if search endpoint found)
# ============================================================
# This will run if we found a working search endpoint above

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("DISCOVERY SUMMARY")
print("=" * 70)
print(f"  Existing dramas in DB: {len(existing_ids)}")
print(f"  NEW dramas found: {len(all_found)}")
if all_found:
    print(f"\n  Sample new dramas:")
    for pid, title in list(all_found.items())[:10]:
        print(f"    - [{pid}] {title}")
