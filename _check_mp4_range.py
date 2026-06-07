#!/usr/bin/env python3
"""Check if dramas in range 150-199 have MP4 files converted."""
import boto3, os

# Load env
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

r2 = boto3.client('s3',
    endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
    region_name='auto')

bucket = os.environ['R2_BUCKET_NAME']

# List all flickreels folders
paginator = r2.get_paginator('list_objects_v2')
folders = set()
for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
    for p in page.get('CommonPrefixes', []):
        folders.add(p['Prefix'])

folders = sorted(folders)
print(f"Total flickreels folders: {len(folders)}")

# Check dramas 150-199
selected = folders[150:200]
print(f"Checking index 150-199 ({len(selected)} dramas)...\n")

no_mp4 = []
ok_count = 0
for i, folder in enumerate(selected):
    name = folder.replace('flickreels/', '').rstrip('/')
    try:
        r2.head_object(Bucket=bucket, Key=f"{folder}ep_001.mp4")
        ok_count += 1
    except:
        no_mp4.append((150 + i, name))

print(f"✅ Has MP4: {ok_count}/{len(selected)}")
print(f"❌ Missing MP4: {len(no_mp4)}/{len(selected)}")
if no_mp4:
    print("\nMissing:")
    for idx, n in no_mp4:
        print(f"  [{idx}] {n}")
else:
    print("\nAll 50 dramas have MP4! ✅")
