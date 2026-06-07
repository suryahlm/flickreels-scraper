import json
import requests
from pathlib import Path

# Load scraping data
with open('Scraping 01/30.01.2026/dramas.json', 'r', encoding='utf-8') as f:
    dramas_data = json.load(f)

# Get drama 3108
drama_id = '3108'
drama = dramas_data.get(drama_id, {})

if not drama:
    print(f"Drama {drama_id} not found in scraping data")
    exit(1)

title = drama.get('title', '')
cover_url = drama.get('cover_url', '')

print(f"Drama: {title}")
print(f"Cover URL: {cover_url}")

if not cover_url:
    print("No cover URL found!")
    exit(1)

# Download cover
drama_folder = Path(f"Video Drama TS/30.01.2026/{title} ({drama_id})")
cover_path = drama_folder / "cover.jpg"

if cover_path.exists():
    print(f"Cover already exists: {cover_path}")
else:
    print(f"Downloading cover to {cover_path}...")
    try:
        response = requests.get(cover_url, timeout=30)
        response.raise_for_status()
        
        with open(cover_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {len(response.content)} bytes")
    except Exception as e:
        print(f"❌ Error: {e}")
