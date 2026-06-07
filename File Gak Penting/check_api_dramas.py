import requests

r = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/r2-dramas',
    headers={'Cache-Control': 'no-cache'}
)
d = r.json()

dramas = d.get('dramas', [])
print(f"API Drama Count: {len(dramas)}")
print(f"Source: {d.get('source')}")
print(f"Cached: {d.get('cached')}")

print(f"\nFirst 10 drama titles:")
for i, dr in enumerate(dramas[:10]):
    print(f"{i+1}. {dr['title']} (ID: {dr['id']})")

# Check for duplicates
ids = [dr['id'] for dr in dramas]
unique_ids = set(ids)
print(f"\nTotal dramas: {len(ids)}")
print(f"Unique IDs: {len(unique_ids)}")
if len(ids) != len(unique_ids):
    print("⚠️ DUPLICATES DETECTED!")
    from collections import Counter
    duplicates = [id for id, count in Counter(ids).items() if count > 1]
    print(f"Duplicate IDs: {duplicates}")
