import requests

print("Checking R2 dramas via API...")
r = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/r2-dramas',
    headers={'Cache-Control': 'no-cache'}
)

if r.status_code == 200:
    data = r.json()
    dramas = data.get('dramas', [])
    
    print(f"\n✅ R2 Status:")
    print(f"Total dramas in R2: {len(dramas)}")
    print(f"Source: {data.get('source', 'unknown')}")
    print(f"Cached: {data.get('cached', 'N/A')}")
    
    if len(dramas) > 0:
        print(f"\nDrama list:")
        for i, d in enumerate(dramas, 1):
            title = d.get('title', 'NO TITLE')
            episodes = d.get('total_episodes', 0)
            drama_id = d.get('id', 'NO ID')
            print(f"{i}. {title} - {episodes} eps (ID: {drama_id})")
    
    # Calculate upload progress
    total_expected = 48  # Total dramas scraped
    uploaded = len(dramas)
    percent = (uploaded / total_expected) * 100
    
    print(f"\n📊 Upload Progress:")
    print(f"Uploaded: {uploaded}/{total_expected} dramas ({percent:.1f}%)")
    print(f"Remaining: {total_expected - uploaded} dramas")
else:
    print(f"❌ API Error: {r.status_code}")
    print(r.text[:500])
