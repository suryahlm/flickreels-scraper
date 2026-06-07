#!/usr/bin/env python3
"""Download dramas from R2 with 10 concurrent workers + cover images"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import boto3
import threading

load_dotenv()

BUCKET = os.environ.get('R2_BUCKET_NAME', 'asiandrama-cdn')
OUTPUT_DIR = r"D:\Surya\IT\AsianDrama-02\Drama untuk Tiktok"
WORKERS = 10

# Thread-local R2 clients
_local = threading.local()
def get_r2():
    if not hasattr(_local, 'r2'):
        _local.r2 = boto3.client('s3',
            endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
            region_name='auto'
        )
    return _local.r2

r2 = get_r2()

# Find drama folders
print("📂 Finding drama folders in R2...")
folders = []
resp = r2.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/')
for p in resp.get('CommonPrefixes', []):
    folders.append(p['Prefix'])
while resp.get('IsTruncated'):
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/', ContinuationToken=resp['NextContinuationToken'])
    for p in resp.get('CommonPrefixes', []):
        folders.append(p['Prefix'])

# Search for the 3 dramas
SEARCH = ['peramal wanita', 'tak bisa melepasmu', 'tiada maaf bagimu']
matched = []
for search in SEARCH:
    for folder in folders:
        name = folder.rstrip('/').split('/')[-1].lower()
        if search in name:
            matched.append(folder)
            break
    else:
        print(f"  ❌ Not found: '{search}'")

print(f"\n✅ Found {len(matched)} dramas:")
for m in matched:
    print(f"   - {m.rstrip('/').split('/')[-1]}")

def download_file(args):
    """Download a single file from R2. Thread-safe."""
    r2_key, local_path, expected_size = args
    r2c = get_r2()
    
    # Skip if already exists with correct size
    if os.path.exists(local_path) and os.path.getsize(local_path) == expected_size:
        return ('skipped', r2_key)
    
    try:
        r2c.download_file(BUCKET, r2_key, local_path)
        return ('success', r2_key)
    except Exception as e:
        return ('failed', f"{r2_key}: {e}")

# Download each drama
for drama_prefix in matched:
    drama_name = drama_prefix.rstrip('/').split('/')[-1]
    # Clean folder name: remove ID suffix + trailing spaces
    clean_name = drama_name.rsplit(' (', 1)[0].strip() if ' (' in drama_name else drama_name.strip()
    
    local_dir = os.path.join(OUTPUT_DIR, clean_name)
    os.makedirs(local_dir, exist_ok=True)
    
    # List all files (MP4 + covers)
    print(f"\n🎬 {drama_name}")
    all_files = []
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=drama_prefix)
    all_files.extend(resp.get('Contents', []))
    while resp.get('IsTruncated'):
        resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=drama_prefix, ContinuationToken=resp['NextContinuationToken'])
        all_files.extend(resp.get('Contents', []))
    
    # Filter: MP4 + cover images
    downloads = []
    for obj in all_files:
        key = obj['Key']
        filename = key.split('/')[-1]
        if filename.endswith('.mp4') or filename.startswith('cover.'):
            local_path = os.path.join(local_dir, filename)
            downloads.append((key, local_path, obj['Size']))
    
    downloads.sort(key=lambda x: x[0])
    
    mp4_count = sum(1 for d in downloads if d[0].endswith('.mp4'))
    cover_count = sum(1 for d in downloads if 'cover.' in d[0])
    total_mb = sum(d[2] for d in downloads) / 1024 / 1024
    print(f"   📋 {mp4_count} episodes + {cover_count} covers ({total_mb:.0f} MB total)")
    print(f"   🔧 {WORKERS} workers")
    
    success = 0
    skipped = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(download_file, d): d for d in downloads}
        for i, future in enumerate(as_completed(futures), 1):
            status, info = future.result()
            filename = info.split('/')[-1] if status != 'failed' else info
            if status == 'success':
                success += 1
                print(f"   ✅ [{i}/{len(downloads)}] {filename}")
            elif status == 'skipped':
                skipped += 1
                print(f"   ⏭️  [{i}/{len(downloads)}] {filename}")
            else:
                failed += 1
                print(f"   ❌ [{i}/{len(downloads)}] {filename}")
    
    print(f"   📊 ✅{success} ⏭️{skipped} ❌{failed}")

print(f"\n🏁 Done! Files saved to: {OUTPUT_DIR}")
