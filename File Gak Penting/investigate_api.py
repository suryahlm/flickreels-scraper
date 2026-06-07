#!/usr/bin/env python3
"""Deep investigation of API and R2 issues."""
import requests
import time
import json

print("=" * 60)
print("ASIANDRAMA API DEEP INVESTIGATION")
print("=" * 60)

# 1. Test API Response Time
print("\n1. Testing API Response Time...")
api_url = "https://tender-connection-production-246f.up.railway.app/api/r2-dramas"

start = time.time()
try:
    r = requests.get(api_url, timeout=120)
    elapsed = time.time() - start
    print(f"   Time: {elapsed:.1f}s")
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        dramas = data.get("dramas", [])
        print(f"   Drama count: {len(dramas)}")
        print(f"   Source: {data.get('source', 'unknown')}")
        print(f"   Cache: {r.headers.get('X-Cache', 'unknown')}")
        
        # 2. Check first few dramas
        print("\n2. Checking First 5 Dramas...")
        for i, d in enumerate(dramas[:5]):
            print(f"\n   [{i+1}] {d.get('title', 'NO TITLE')}")
            print(f"       ID: {d.get('id')}")
            print(f"       Cover URL: {d.get('cover_url', 'NONE')[:80]}...")
            print(f"       Episodes: {d.get('total_episodes')}")
        
        # 3. Test cover URL accessibility
        print("\n3. Testing Cover URL Accessibility...")
        test_dramas = dramas[:3]
        for d in test_dramas:
            cover_url = d.get("cover_url", "")
            if cover_url:
                try:
                    cr = requests.head(cover_url, timeout=10)
                    print(f"   {d.get('title', 'NO TITLE')[:30]}: {cr.status_code}")
                except Exception as e:
                    print(f"   {d.get('title', 'NO TITLE')[:30]}: ERROR - {e}")
        
        # 4. Check dramas without covers in app
        print("\n4. Checking Drama Data Quality...")
        no_cover = [d for d in dramas if not d.get("cover_url")]
        no_episodes = [d for d in dramas if not d.get("total_episodes")]
        print(f"   Dramas without cover_url: {len(no_cover)}")
        print(f"   Dramas without episodes: {len(no_episodes)}")
        
    else:
        print(f"   ERROR: {r.text[:500]}")
        
except requests.Timeout:
    print(f"   TIMEOUT after 120s!")
except Exception as e:
    print(f"   ERROR: {e}")

# 5. Direct R2 test
print("\n5. Testing Direct R2 Stream Endpoint...")
test_urls = [
    "/api/stream/flickreels/Romansa%20Om%20(5099)/cover.jpg",
    "/api/stream/flickreels/Tak%20Bisa%20Melepasmu%20(2858)/cover.jpg"
]
base = "https://tender-connection-production-246f.up.railway.app"
for path in test_urls:
    try:
        r = requests.head(base + path, timeout=10)
        print(f"   {path[-40:]}: {r.status_code}")
    except Exception as e:
        print(f"   {path[-40:]}: ERROR - {e}")

print("\n" + "=" * 60)
print("INVESTIGATION COMPLETE")
print("=" * 60)
