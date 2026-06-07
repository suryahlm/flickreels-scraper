import requests

# Check /api/dramas (old FlickReels endpoint)
print("=" * 50)
print("Checking /api/dramas (FlickReels API)")
print("=" * 50)
r = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/dramas',
)
try:
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, dict):
            dramas = data.get('dramas', data.get('data', []))
        elif isinstance(data, list):
            dramas = data
        else:
            dramas = []
        
        print(f"Status: {r.status_code}")
        print(f"Drama count: {len(dramas)}")
        if dramas:
            print(f"\nFirst 5:")
            for i, d in enumerate(dramas[:5]):
                title = d.get('title', d.get('name', 'NO TITLE'))
                print(f"{i+1}. {title}")
    else:
        print(f"Status: {r.status_code}")
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Error parsing: {e}")

print("\n" + "=" * 50)
print("Checking /api/r2-dramas")
print("=" * 50)
r2 = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/r2-dramas',
    headers={'Cache-Control': 'no-cache'}
)
d2 = r2.json()
print(f"Status: {r2.status_code}")
print(f"Drama count: {len(d2.get('dramas', []))}")
