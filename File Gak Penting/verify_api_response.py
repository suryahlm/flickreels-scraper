import requests

print("Checking what API is ACTUALLY returning right now...\n")

response = requests.get("https://tender-connection-production-246f.up.railway.app/api/r2-dramas")

if response.status_code == 200:
    data = response.json()
    dramas = data.get('dramas', [])
    
    if dramas:
        sample = dramas[0]
        print(f"Sample drama: {sample['title']}\n")
        print(f"ID: {sample['id']}")
        print(f"cover_url: {sample.get('cover_url', 'MISSING')}")
        print(f"thumbnail_url: {sample.get('thumbnail_url', 'MISSING')}\n")
        
        # Check if URLs are absolute
        cover = sample.get('cover_url', '')
        thumb = sample.get('thumbnail_url', '')
        
        print("URL Types:")
        print(f"  cover_url: {'✅ Absolute' if cover.startswith('http') else '❌ Relative'}")
        print(f"  thumbnail_url: {'✅ Absolute' if thumb.startswith('http') else '❌ Relative'}")
        
        # Test actual image load
        print(f"\nTesting image accessibility...")
        try:
            img_resp = requests.head(cover, timeout=5)
            print(f"  Cover HTTP Status: {img_resp.status_code}")
            if img_resp.status_code == 200:
                print(f"  ✅ IMAGE ACCESSIBLE")
            else:
                print(f"  ❌ IMAGE NOT ACCESSIBLE")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print("❌ No dramas in response")
else:
    print(f"❌ API Error: {response.status_code}")
