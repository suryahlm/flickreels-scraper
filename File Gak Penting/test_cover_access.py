import requests
import time

print("Checking cover URLs from API...\n")

# Bust cache
url = f"https://tender-connection-production-246f.up.railway.app/api/r2-dramas?v={int(time.time())}"

response = requests.get(url, headers={'Cache-Control': 'no-cache'})

if response.status_code == 200:
    data = response.json()
    dramas = data.get('dramas', [])
    
    print(f"Total dramas in API: {len(dramas)}\n")
    print("="*60)
    print("Testing cover accessibility...\n")
    
    accessible = []
    broken = []
    
    for drama in dramas:
        title = drama['title']
        cover_url = drama.get('cover_url', '')
        
        if cover_url:
            try:
                resp = requests.head(cover_url, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    accessible.append(title)
                    print(f"✅ {title[:50]}")
                else:
                    broken.append(title)
                    print(f"❌ {title[:50]} - Status {resp.status_code}")
            except Exception as e:
                broken.append(title)
                print(f"❌ {title[:50]} - {str(e)[:30]}")
        else:
            broken.append(title)
            print(f"❌ {title[:50]} - No URL")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✅ Accessible covers: {len(accessible)}")
    print(f"  ❌ Broken/missing: {len(broken)}")
    print(f"{'='*60}\n")
    
    if broken:
        print("Dramas with broken covers:")
        for title in broken:
            print(f"  - {title}")
else:
    print(f"❌ API Error: {response.status_code}")
