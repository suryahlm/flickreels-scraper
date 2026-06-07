#!/usr/bin/env python3
"""
Break the 495 wall - Multi-strategy Indonesian drama discovery
==============================================================
Strategy 1: Analyze existing ID range + pattern
Strategy 2: Check chapterList response for recommendation fields
Strategy 3: ID Brute-Force scan with language verification
Strategy 4: Search with connector words (yang, di, ke, aku, kamu)
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import time
from local_scraping_indonesia import (
    IndonesianAPI, generate_sign, generate_nonce,
    FLICKREELS_CONFIG, INDONESIAN_BODY, SUPABASE_CONFIG,
    rate_limiter
)

def api_request(endpoint, extra_body=None):
    body = {**INDONESIAN_BODY, **(extra_body or {})}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    headers = {
        "token": FLICKREELS_CONFIG["token"],
        "sign": sign, "timestamp": timestamp, "nonce": nonce,
        "version": FLICKREELS_CONFIG["version"],
        "content-type": "application/json"
    }
    try:
        rate_limiter.acquire()
        resp = requests.post(
            f"{FLICKREELS_CONFIG['base_url']}{endpoint}",
            json=body, headers=headers, timeout=15
        )
        return resp.json()
    except Exception as e:
        return {"status_code": -1, "msg": str(e)}

# ============================================================
# STRATEGY 1: Analyze existing ID range
# ============================================================
print("=" * 70)
print("STRATEGY 1: Analyze existing drama IDs")
print("=" * 70)

resp = requests.get(
    f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id&order=flickreels_id.asc",
    headers={"apikey": SUPABASE_CONFIG["key"]}
)
existing_ids = []
if resp.status_code == 200:
    for d in resp.json():
        fid = d.get('flickreels_id')
        if fid:
            try:
                existing_ids.append(int(fid))
            except:
                existing_ids.append(fid)

existing_set = set(str(i) for i in existing_ids)
numeric_ids = sorted([i for i in existing_ids if isinstance(i, int)])

if numeric_ids:
    print(f"  Total existing: {len(existing_ids)}")
    print(f"  Numeric IDs: {len(numeric_ids)}")
    print(f"  Min ID: {min(numeric_ids)}")
    print(f"  Max ID: {max(numeric_ids)}")
    print(f"  Range span: {max(numeric_ids) - min(numeric_ids)}")
    print(f"  First 10: {numeric_ids[:10]}")
    print(f"  Last 10: {numeric_ids[-10:]}")
    
    # Gaps analysis
    gaps = []
    for i in range(len(numeric_ids) - 1):
        gap = numeric_ids[i+1] - numeric_ids[i]
        if gap > 1:
            gaps.append((numeric_ids[i], numeric_ids[i+1], gap))
    
    print(f"\n  Total gaps: {len(gaps)}")
    print(f"  Largest gaps:")
    for start, end, size in sorted(gaps, key=lambda x: -x[2])[:10]:
        print(f"    {start} -> {end} (gap: {size})")
    
    # Unchecked IDs in range
    all_in_range = set(range(min(numeric_ids), max(numeric_ids) + 1))
    unchecked = all_in_range - set(numeric_ids)
    print(f"\n  IDs NOT in our DB within range: {len(unchecked)}")
else:
    print("  No numeric IDs found!")

# ============================================================
# STRATEGY 2: Check chapterList response for recommendation fields
# ============================================================
print("\n" + "=" * 70)
print("STRATEGY 2: Inspect chapterList response for hidden fields")
print("=" * 70)

# Pick 3 random dramas and inspect FULL response
sample_ids = numeric_ids[:1] + numeric_ids[len(numeric_ids)//2:len(numeric_ids)//2+1] + numeric_ids[-1:]
for drama_id in sample_ids:
    result = api_request("/app/playlet/chapterList", {"playlet_id": str(drama_id)})
    if result.get("status_code") == 1:
        data = result.get("data", {})
        print(f"\n  Drama ID {drama_id}: {data.get('title', 'N/A')}")
        print(f"  Response keys: {list(data.keys())}")
        
        # Look for recommendation-related fields
        for key in data.keys():
            val = data[key]
            if isinstance(val, list) and key != 'list':  # 'list' = episodes
                print(f"    📌 '{key}' = list with {len(val)} items")
                if val and isinstance(val[0], dict):
                    print(f"       First item keys: {list(val[0].keys())[:8]}")
            elif isinstance(val, dict) and key not in ['list']:
                print(f"    📌 '{key}' = dict with keys: {list(val.keys())[:8]}")
    time.sleep(0.3)

# Also try some recommendation-specific endpoints
print("\n  Testing recommendation endpoints:")
for ep in [
    "/app/playlet/guessLike",
    "/app/playlet/relatedList",
    "/app/playlet/recommendList",
    "/app/playlet/moreRecommend",
    "/app/playlet/relatePlaylet",
]:
    result = api_request(ep, {"playlet_id": str(numeric_ids[0])})
    status = result.get('status_code')
    msg = result.get('msg', '')[:50]
    if status == 1:
        data = result.get('data', {})
        if isinstance(data, list):
            print(f"  ✅ {ep}: {len(data)} items")
        elif isinstance(data, dict):
            items = data.get('list', [])
            print(f"  ✅ {ep}: {len(items)} items")
    else:
        print(f"  ❌ {ep}: {msg}")
    time.sleep(0.3)

# ============================================================
# STRATEGY 3: Quick ID Brute-Force scan (sample range)
# ============================================================
print("\n" + "=" * 70)
print("STRATEGY 3: ID Brute-Force scan (sampling)")
print("=" * 70)

if numeric_ids:
    max_id = max(numeric_ids)
    # Scan beyond max ID
    print(f"  Scanning above max ID ({max_id}) up to {max_id + 200}...")
    new_indonesian = []
    not_found = 0
    
    for scan_id in range(max_id + 1, max_id + 201):
        if str(scan_id) in existing_set:
            continue
        result = api_request("/app/playlet/chapterList", {"playlet_id": str(scan_id)})
        if result.get("status_code") == 1:
            data = result.get("data", {})
            title = data.get("title", "")
            lang = data.get("language_name", "").lower()
            eps = len(data.get("list", []))
            
            if "indonesian" in lang or "indonesia" in lang:
                print(f"  ✅ [{scan_id}] {title} — Indonesian ({eps} eps)")
                new_indonesian.append(scan_id)
            else:
                print(f"  ⚪ [{scan_id}] {title} — {lang} ({eps} eps)")
        else:
            not_found += 1
        
        time.sleep(0.15)
    
    print(f"\n  Scanned: 200 IDs above max")
    print(f"  Not found: {not_found}")
    print(f"  New Indonesian: {len(new_indonesian)}")
    
    # Also scan gaps within existing range (sample large gaps)
    large_gaps = sorted(gaps, key=lambda x: -x[2])[:5]
    gap_indonesian = []
    
    if large_gaps:
        print(f"\n  Sampling largest gaps:")
        for start, end, size in large_gaps:
            # Sample up to 20 IDs from each gap
            step = max(1, size // 20)
            found_in_gap = 0
            for scan_id in range(start + 1, end, step):
                if str(scan_id) in existing_set:
                    continue
                result = api_request("/app/playlet/chapterList", {"playlet_id": str(scan_id)})
                if result.get("status_code") == 1:
                    data = result.get("data", {})
                    lang = data.get("language_name", "").lower()
                    if "indonesian" in lang:
                        title = data.get("title", "")
                        print(f"    ✅ [{scan_id}] {title} — Indonesian")
                        gap_indonesian.append(scan_id)
                        found_in_gap += 1
                time.sleep(0.15)
            print(f"    Gap {start}-{end}: {found_in_gap} Indonesian found")
        
        print(f"  Total from gaps: {len(gap_indonesian)}")

# ============================================================
# STRATEGY 4: Search with connector words
# ============================================================
print("\n" + "=" * 70)
print("STRATEGY 4: Search with connector/common words")
print("=" * 70)

connector_words = ["yang", "di", "ke", "dan", "ini", "itu", "si", "sang", "para"]
all_search_new = {}

for kw in connector_words:
    for page in range(1, 6):
        result = api_request("/app/user_search/search", {
            "keyword": kw, "page": page, "page_size": 50
        })
        if result.get("status_code") != 1:
            break
        data = result.get("data", {})
        items = data.get("list", []) if isinstance(data, dict) else []
        if not items:
            break
        
        new = 0
        for item in items:
            pid = str(item.get("playlet_id", ""))
            if pid and pid not in existing_set and pid not in all_search_new:
                all_search_new[pid] = item.get("title", "")
                new += 1
        
        if new > 0:
            print(f"  Search \"{kw}\" p{page}: {len(items)} results, {new} NEW")
        if len(items) < 50:
            break
        time.sleep(0.2)
    time.sleep(0.1)

print(f"\n  New from connector search: {len(all_search_new)}")
if all_search_new:
    # Verify language for search results
    print("  Verifying language...")
    search_indonesian = []
    for pid, title in list(all_search_new.items())[:20]:
        result = api_request("/app/playlet/chapterList", {"playlet_id": pid})
        if result.get("status_code") == 1:
            data = result.get("data", {})
            lang = data.get("language_name", "").lower()
            if "indonesian" in lang:
                print(f"    ✅ [{pid}] {title[:40]} — Indonesian")
                search_indonesian.append(pid)
            else:
                print(f"    ⚪ [{pid}] {title[:40]} — {lang}")
        time.sleep(0.2)
    print(f"  Verified Indonesian from search: {len(search_indonesian)}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL DISCOVERY SUMMARY")
print("=" * 70)
total_new = len(new_indonesian) + len(gap_indonesian) + len(search_indonesian if 'search_indonesian' in dir() else [])
print(f"  Existing in DB: {len(existing_ids)}")
print(f"  New from ID scan (above max): {len(new_indonesian)}")
print(f"  New from gap scanning: {len(gap_indonesian)}")
print(f"  New from connector search: {len(search_indonesian) if 'search_indonesian' in dir() else 0}")
print(f"  TOTAL NEW INDONESIAN: {total_new}")
