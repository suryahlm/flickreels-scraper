import requests
import time

print("Testing Railway API after deploy...\n")

# Add timestamp to bust cache
url = f"https://tender-connection-production-246f.up.railway.app/api/r2-dramas?bust={int(time.time())}"

response = requests.get(url, headers={'Cache-Control': 'no-cache'})

if response.status_code == 200:
    data = response.json()
    dramas = data.get('dramas', [])
    
    if dramas:
        sample = dramas[0]
        cover_url = sample.get('cover_url', '')
        
        print(f"Sample drama: {sample['title']}")
        print(f"Cover URL: {cover_url}\n")
        
        if cover_url.startswith('http'):
            print("✅ FIXED! URLs are now absolute!")
        else:
            print(f"❌ Still relative - cache not invalidated yet")
            print("   Wait 1 hour or restart Railway service")
    else:
        print("❌ No dramas returned")
else:
    print(f"❌ API error: {response.status_code}")
