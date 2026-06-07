#!/usr/bin/env python3
"""
Quick test of search and ranking
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

# Test search
print("Testing search...")
for keyword in ["cinta", "mafia", "boss"]:
    result = api_request("/app/playlet/search", {"keyword": keyword, "page": 1, "page_size": 100})
    if result.get('status_code') == 1:
        data = result.get('data', {})
        items = data.get('list', []) if isinstance(data, dict) else data
        total = data.get('total') if isinstance(data, dict) else len(data)
        print(f"  Search '{keyword}': {len(items)} results, total={total}")
    else:
        print(f"  Search '{keyword}': {result.get('msg')}")
    time.sleep(0.3)

# Test hot/recommend
print("\nTesting hot/recommend...")
for endpoint in ["/app/playlet/hot", "/app/playlet/recommend"]:
    result = api_request(endpoint, {"page": 1, "page_size": 100})
    if result.get('status_code') == 1:
        data = result.get('data', {})
        if isinstance(data, list):
            print(f"  {endpoint}: {len(data)} items")
        elif isinstance(data, dict):
            items = data.get('list', [])
            print(f"  {endpoint}: {len(items)} items")
    else:
        print(f"  {endpoint}: {result.get('msg')}")
    time.sleep(0.3)

# Test ranking
print("\nTesting ranking with different types...")
for ranktype in [1, 2, 3, 4, 5]:
    result = api_request("/app/playlet/rankingList", {"type": ranktype, "page": 1, "page_size": 100})
    if result.get('status_code') == 1:
        data = result.get('data', {})
        items = data.get('list', []) if isinstance(data, dict) else data
        print(f"  Ranking type {ranktype}: {len(items)} items")
    else:
        print(f"  Ranking type {ranktype}: {result.get('msg')}")
    time.sleep(0.2)
