import requests
import time

# Check production with cache bypass
headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
r = requests.get('https://tender-connection-production-246f.up.railway.app/api/r2-dramas', headers=headers)
d = r.json()
print(f"Production count: {d.get('count', 0)}")
print(f"Cache: {r.headers.get('X-Cache', 'N/A')}")
print(f"Source: {d.get('source', 'N/A')}")
print("\nDramas:")
for drama in d.get('dramas', []):
    print(f"  - {drama['title']} ({drama.get('total_episodes', 0)} eps)")
