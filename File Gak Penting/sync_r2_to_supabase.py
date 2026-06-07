"""
Sync R2 Dramas to Supabase
==========================
Imports all dramas from R2 storage to Supabase database
so they can be managed via Admin Portal.
"""

import json
import boto3
from botocore.config import Config
import requests

# R2 Configuration
R2_CONFIG = {
    "account_id": "caa84fe6b1be065cda3836f0dac4b509",
    "access_key": "a4903ea93c248388b6e295d6cdbc8617",
    "secret_key": "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9",
    "bucket": "asiandrama-cdn",
}

# Supabase Configuration
SUPABASE_URL = "https://wgmhfsvthqsnxqodwocx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndnbWhmc3Z0aHFzbnhxb2R3b2N4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc5NDg2NDgsImV4cCI6MjA1MzUyNDY0OH0.WKVn-Ri3I_7_Shg7zJtZxfB7sLNdcDnqMgKQIc5KzYk"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def supabase_select(table, columns="*", filters=None):
    """SELECT from Supabase table"""
    url = f"{SUPABASE_URL}/rest/v1/{table}?select={columns}"
    if filters:
        url += f"&{filters}"
    resp = requests.get(url, headers=HEADERS)
    return resp.json() if resp.status_code == 200 else []

def supabase_insert(table, data):
    """INSERT into Supabase table"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.post(url, headers=HEADERS, json=data)
    return resp.status_code in [200, 201]

def main():
    print("=" * 60)
    print("SYNC R2 DRAMAS TO SUPABASE")
    print("=" * 60)
    
    # Connect to R2
    print("\n[1] Connecting to R2...")
    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_CONFIG['access_key'],
        aws_secret_access_key=R2_CONFIG['secret_key'],
        config=Config(signature_version='s3v4')
    )
    
    # Get existing dramas from Supabase
    print("[2] Fetching existing dramas from Supabase...")
    existing = supabase_select('dramas', 'flickreels_id')
    existing_ids = set(str(d.get('flickreels_id', '')) for d in existing if d.get('flickreels_id'))
    print(f"    Found {len(existing_ids)} existing dramas")
    
    # List R2 folders
    print("[3] Listing R2 folders...")
    paginator = s3.get_paginator('list_objects_v2')
    
    folders = []
    for page in paginator.paginate(Bucket=R2_CONFIG['bucket'], Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folder = prefix['Prefix'].replace('flickreels/', '').rstrip('/')
            if folder and folder not in ['test', 'dramas']:
                folders.append(folder)
    
    print(f"    Found {len(folders)} drama folders in R2")
    
    # Process each folder
    print("\n[4] Syncing dramas to Supabase...")
    synced = 0
    skipped = 0
    failed = 0
    
    for folder in folders:
        # Extract ID from folder name (format: "Title (ID)")
        try:
            drama_id = folder.split('(')[-1].rstrip(')')
            if not drama_id.isdigit():
                drama_id = folder.replace(' ', '_')
        except:
            drama_id = folder.replace(' ', '_')
        
        # Skip if already exists
        if drama_id in existing_ids:
            print(f"  [SKIP] {folder[:50]}...")
            skipped += 1
            continue
        
        # Read metadata from R2
        try:
            meta_response = s3.get_object(
                Bucket=R2_CONFIG['bucket'],
                Key=f"flickreels/{folder}/metadata.json"
            )
            metadata = json.loads(meta_response['Body'].read().decode('utf-8'))
        except Exception as e:
            print(f"  [NO META] {folder[:50]}...")
            failed += 1
            continue
        
        # Check if cover exists
        try:
            s3.head_object(
                Bucket=R2_CONFIG['bucket'],
                Key=f"flickreels/{folder}/cover.jpg"
            )
            has_cover = True
        except:
            has_cover = False
        
        # Count episodes
        episode_count = 0
        try:
            ep_response = s3.list_objects_v2(
                Bucket=R2_CONFIG['bucket'],
                Prefix=f"flickreels/{folder}/ep_",
                MaxKeys=200
            )
            for obj in ep_response.get('Contents', []):
                if obj['Key'].endswith('.m3u8'):
                    episode_count += 1
        except:
            episode_count = metadata.get('total_episodes', 0) or metadata.get('chapter_total', 0)
        
        if episode_count == 0:
            episode_count = metadata.get('total_episodes', 0) or metadata.get('chapter_total', 0)
        
        # Prepare drama data
        title = metadata.get('title', folder.split('(')[0].strip())
        drama_data = {
            'flickreels_id': drama_id,
            'title': title,
            'synopsis': metadata.get('synopsis', ''),
            'cover_url': f"https://tender-connection-production-246f.up.railway.app/api/stream/flickreels/{folder}/cover.jpg" if has_cover else None,
            'total_episodes': episode_count,
            'r2_folder': folder,
            'is_published': True,  # Auto-publish
        }
        
        # Insert to Supabase
        if supabase_insert('dramas', drama_data):
            print(f"  [SYNC] {title[:45]}... ({episode_count} eps)")
            synced += 1
        else:
            print(f"  [ERROR] {folder[:50]}...")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"  Synced: {synced}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Total in Supabase now: {len(existing_ids) + synced}")
    print("=" * 60)

if __name__ == "__main__":
    main()
