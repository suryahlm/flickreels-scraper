"""
Final verification - test actual image loading like mobile app would
"""
import requests
import json
import time

print("FINAL COVER VERIFICATION")
print("="*60)

# Get drama list from API
api_url = f"https://tender-connection-production-246f.up.railway.app/api/r2-dramas?t={int(time.time())}"
response = requests.get(api_url)

if response.status_code != 200:
    print(f"❌ API Error: {response.status_code}")
    exit(1)

dramas = response.json()['dramas']

print(f"Testing {len(dramas)} drama covers...\n")

working = []
broken = []

for drama in dramas:
    title = drama['title']
    # Use thumbnail_url like the app does
    cover_url = drama.get('thumbnail_url') or drama.get('cover_url', '')
    
    if not cover_url:
        broken.append({'title': title, 'reason': 'No URL'})
        print(f"❌ {title[:50]:<50} - No URL")
        continue
    
    # Check if absolute
    if not cover_url.startswith('http'):
        broken.append({'title': title, 'reason': 'Relative URL'})
        print(f"❌ {title[:50]:<50} - Relative URL")
        continue
    
    # Try to fetch image
    try:
        img_resp = requests.get(cover_url, timeout=10)
        if img_resp.status_code == 200:
            # Check if actual image (not error page)
            content_type = img_resp.headers.get('content-type', '')
            if 'image' in content_type:
                working.append(title)
                print(f"✅ {title[:50]:<50}")
            else:
                broken.append({'title': title, 'reason': f'Not image: {content_type}'})
                print(f"❌ {title[:50]:<50} - Not image")
        else:
            broken.append({'title': title, 'reason': f'HTTP {img_resp.status_code}'})
            print(f"❌ {title[:50]:<50} - HTTP {img_resp.status_code}")
    except Exception as e:
        broken.append({'title': title, 'reason': str(e)[:50]})
        print(f"❌ {title[:50]:<50} - {str(e)[:30]}")

print(f"\n{'='*60}")
print(f"RESULTS:")
print(f"  ✅ Working: {len(working)}/{len(dramas)}")
print(f"  ❌ Broken: {len(broken)}/{len(dramas)}")
print(f"{'='*60}\n")

if broken:
    print("Broken covers details:")
    for item in broken:
        print(f"  - {item['title']}")
        print(f"    Reason: {item['reason']}\n")

# Save results
with open('cover_test_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'working': working,
        'broken': broken,
        'total': len(dramas),
        'working_count': len(working),
        'broken_count': len(broken)
    }, f, indent=2, ensure_ascii=False)

print("Results saved to cover_test_results.json")
