import requests
import os
import json
import time
import random
import string
from sign_generator import generate_sign

# Dramas missing cover files
missing_covers = [
    {"name": "Nikah Kontrak Berujung Cinta", "id": "2537"},
    {"name": "Sekata dalam Diam", "id": "1859"},
]

print("Downloading missing covers from FlickReels...\n")

def get_random_nonce(length=32):
    """Generate random nonce"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

for drama in missing_covers:
    drama_id = drama['id']
    drama_name = drama['name']
    
    print(f"Fetching cover for: {drama_name} (ID: {drama_id})")
    
    try:
        # Get drama detail from FlickReels API
        detail_url = f"https://api.flickreels.com/api/app/drama/detail"
        body = {
            'id': drama_id,
            'language_id': '6'
        }
        
        # Generate sign
        timestamp = str(int(time.time()))
        nonce = get_random_nonce()
        sign = generate_sign(body, timestamp, nonce)
        
        params = {
            **body,
            'timestamp': timestamp,
            'nonce': nonce,
            'sign': sign
        }
        
        response = requests.get(detail_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
           
            if data.get('code') == 200:
                drama_data = data.get('data', {})
                cover_url = drama_data.get('cover', '')
                
                if cover_url:
                    print(f"  Cover URL: {cover_url[:80]}...")
                    
                    # Download cover
                    cover_response = requests.get(cover_url, timeout=15)
                    
                    if cover_response.status_code == 200:
                        # Find local folder
                        video_dir = "Video Drama TS/30.01.2026"
                        folders = os.listdir(video_dir)
                        
                        matching_folder = None
                        for folder in folders:
                            if f"({drama_id})" in folder:
                                matching_folder = folder
                                break
                        
                        if matching_folder:
                            cover_path = os.path.join(video_dir, matching_folder, "cover.jpg")
                            
                            with open(cover_path, 'wb') as f:
                                f.write(cover_response.content)
                            
                            size = len(cover_response.content)
                            print(f"  ✅ Downloaded: {size:,} bytes")
                            print(f"  Saved to: {cover_path}\n")
                        else:
                            print(f"  ❌ Folder not found for ID {drama_id}\n")
                    else:
                        print(f"  ❌ Failed to download cover: {cover_response.status_code}\n")
                else:
                    print(f"  ❌ No cover URL in response\n")
            else:
                print(f"  ❌ API error: {data.get('msg')}\n")
        else:
            print(f"  ❌ HTTP {response.status_code}\n")
            
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("="*60)
print("Done downloading covers!")
