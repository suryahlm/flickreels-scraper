import requests
import time

url = f"https://tender-connection-production-246f.up.railway.app/api/r2-dramas?t={int(time.time())}"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    dramas = data['dramas']
    
    print(f"\n✅ Total dramas in API: {len(dramas)}")
    print(f"Expected: 42 (48 original - 6 deleted)\n")
    
    if len(dramas) == 42:
        print("✅ CORRECT! 6 dramas successfully deleted")
    else:
        print(f"⚠️  Expected 42 but got {len(dramas)}")
    
    print("\nSample dramas:")
    for drama in dramas[:5]:
        print(f"  - {drama['title']}")
else:
    print(f"❌ API Error: {response.status_code}")
