"""
Sync R2 Drama to Supabase Database (REST API version)
======================================================
After scraping to R2, run this to add drama to database.

Usage:
    python sync_to_db.py --drama="Forbidden Itch (5301)"
"""
import os
import json
import argparse
import boto3
import requests
from botocore.config import Config

# Configuration
R2_CONFIG = {
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com",
    "access_key": "a4903ea93c248388b6e295d6cdbc8617",
    "secret_key": "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9",
    "bucket": "asiandrama-cdn",
    "public_url": "https://pub-c6622e5cea6d49dbadba93f3b5765f21.r2.dev"
}

# Anon key (from admin .env.local)
SUPABASE_URL = "https://bmryonqbddbkjbtquhgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=R2_CONFIG["endpoint_url"],
        aws_access_key_id=R2_CONFIG["access_key"],
        aws_secret_access_key=R2_CONFIG["secret_key"],
        config=Config(signature_version='s3v4')
    )

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def sync_drama(drama_folder):
    """Sync a drama from R2 to Supabase database"""
    r2 = get_r2_client()
    
    prefix = f"flickreels/{drama_folder}/"
    
    print(f"📂 Syncing: {drama_folder}")
    
    # Get metadata.json from R2
    try:
        response = r2.get_object(Bucket=R2_CONFIG["bucket"], Key=f"{prefix}metadata.json")
        metadata = json.loads(response['Body'].read().decode('utf-8'))
        print(f"  ✅ Found metadata: {metadata.get('title')}")
    except Exception as e:
        print(f"  ❌ No metadata.json found: {e}")
        return False
    
    # Get list of episodes (.m3u8 files)
    result = r2.list_objects_v2(Bucket=R2_CONFIG["bucket"], Prefix=prefix)
    episode_files = [obj['Key'] for obj in result.get('Contents', []) if obj['Key'].endswith('.m3u8')]
    episode_files.sort()
    
    print(f"  📺 Found {len(episode_files)} episodes")
    
    # Build URLs
    cover_url = f"{R2_CONFIG['public_url']}/{prefix}cover.jpg"
    
    # Check if drama already exists
    check_url = f"{SUPABASE_URL}/rest/v1/dramas?title=eq.{requests.utils.quote(metadata.get('title'))}"
    existing = requests.get(check_url, headers=supabase_headers()).json()
    
    if existing and len(existing) > 0:
        print(f"  ⚠️ Drama already exists (id: {existing[0]['id']})")
        drama_id = existing[0]['id']
    else:
        # Insert drama
        drama_data = {
            "title": metadata.get('title', drama_folder),
            "synopsis": f"Drama dengan {len(episode_files)} episode",
            "thumbnail_url": cover_url,
            "total_episodes": len(episode_files),
            "is_published": True,
            "view_count": 0
        }
        
        insert_url = f"{SUPABASE_URL}/rest/v1/dramas"
        result = requests.post(insert_url, headers=supabase_headers(), json=drama_data)
        
        if result.status_code in [200, 201]:
            drama_id = result.json()[0]['id']
            print(f"  ✅ Drama inserted (id: {drama_id})")
        else:
            print(f"  ❌ Insert failed: {result.text}")
            return False
    
    # Insert episodes
    inserted = 0
    for i, ep_file in enumerate(episode_files, 1):
        video_url = f"{R2_CONFIG['public_url']}/{ep_file}"
        
        # Check if episode exists
        check_ep_url = f"{SUPABASE_URL}/rest/v1/episodes?drama_id=eq.{drama_id}&episode_number=eq.{i}"
        existing_ep = requests.get(check_ep_url, headers=supabase_headers()).json()
        
        if existing_ep:
            continue  # Skip existing
        
        episode_data = {
            "drama_id": drama_id,
            "episode_number": i,
            "title": f"Episode {i}",
            "video_url": video_url,
            "is_vip": False,
            "coin_cost": 0
        }
        
        insert_ep_url = f"{SUPABASE_URL}/rest/v1/episodes"
        result = requests.post(insert_ep_url, headers=supabase_headers(), json=episode_data)
        
        if result.status_code in [200, 201]:
            inserted += 1
    
    print(f"  📺 Inserted {inserted} new episodes")
    print(f"\n✅ Sync complete! Drama '{metadata.get('title')}' is now in database.")
    return True

def list_r2_dramas():
    """List all drama folders in R2"""
    r2 = get_r2_client()
    
    result = r2.list_objects_v2(Bucket=R2_CONFIG["bucket"], Prefix="flickreels/", Delimiter="/")
    
    folders = []
    for prefix in result.get('CommonPrefixes', []):
        folder = prefix['Prefix'].replace('flickreels/', '').rstrip('/')
        folders.append(folder)
    
    return folders

def main():
    parser = argparse.ArgumentParser(description='Sync R2 drama to Supabase database')
    parser.add_argument('--drama', type=str, help='Drama folder name')
    parser.add_argument('--list', action='store_true', help='List all dramas in R2')
    parser.add_argument('--sync-all', action='store_true', help='Sync all dramas')
    args = parser.parse_args()
    
    if args.list:
        folders = list_r2_dramas()
        print(f"Dramas in R2 ({len(folders)} total):")
        for f in folders:
            print(f"  - {f}")
    elif args.sync_all:
        folders = list_r2_dramas()
        print(f"Syncing {len(folders)} dramas...")
        for f in folders:
            sync_drama(f)
            print()
    elif args.drama:
        sync_drama(args.drama)
    else:
        print("Usage:")
        print('  python sync_to_db.py --list')
        print('  python sync_to_db.py --drama="Forbidden Itch (5301)"')
        print('  python sync_to_db.py --sync-all')

if __name__ == "__main__":
    main()
