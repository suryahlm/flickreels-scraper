import requests
import json

print("Checking which dramas are missing covers...\n")

# Fetch drama list from API
response = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/r2-dramas',
    headers={'Cache-Control': 'no-cache'}
)

data = response.json()
dramas = data.get('dramas', [])

print(f"Total dramas: {len(dramas)}\n")

# Check cover URLs
missing_covers = []
has_covers = []

for drama in dramas:
    title = drama.get('title', 'Unknown')
    cover_url = drama.get('cover_url', '')
    drama_id = drama.get('id', '')
    
    if not cover_url or cover_url == '':
        missing_covers.append({
            'id': drama_id,
            'title': title,
            'folder': drama.get('folder_name', '')
        })
        print(f"❌ Missing: {title} (ID: {drama_id})")
    else:
        has_covers.append(title)
        # Verify cover is actually accessible
        try:
            cover_response = requests.head(cover_url, timeout=5)
            if cover_response.status_code != 200:
                print(f"⚠️  Cover URL broken: {title} - Status {cover_response.status_code}")
                missing_covers.append({
                    'id': drama_id,
                    'title': title,
                    'folder': drama.get('folder_name', ''),
                    'broken_url': cover_url
                })
        except Exception as e:
            print(f"⚠️  Can't verify: {title} - {e}")

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  ✅ Has covers: {len(has_covers)}")
print(f"  ❌ Missing covers: {len(missing_covers)}")
print(f"{'='*60}\n")

if missing_covers:
    print("Dramas needing cover fix:")
    for drama in missing_covers:
        print(f"  - {drama['title']} (ID: {drama['id']})")
        print(f"    Folder: {drama['folder']}\n")
    
    # Save to file for fixing
    with open('missing_covers.json', 'w', encoding='utf-8') as f:
        json.dump(missing_covers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to missing_covers.json")
else:
    print("✅ All dramas have covers!")
