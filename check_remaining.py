#!/usr/bin/env python3
"""Quick check: how many dramas still have HLS (not yet converted to MP4)"""
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

r2 = boto3.client('s3',
    endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
    region_name='auto'
)
BUCKET = os.environ.get('R2_BUCKET_NAME', 'asiandrama-cdn')

# List all drama folders
print("📂 Listing all drama folders...")
folders = []
resp = r2.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/')
for p in resp.get('CommonPrefixes', []):
    folders.append(p['Prefix'])
while resp.get('IsTruncated'):
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/', ContinuationToken=resp['NextContinuationToken'])
    for p in resp.get('CommonPrefixes', []):
        folders.append(p['Prefix'])
folders.sort()
print(f"   Total dramas: {len(folders)}")

hls_only = []
mp4_done = 0

for i, folder in enumerate(folders):
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=folder, MaxKeys=5)
    contents = resp.get('Contents', [])
    keys = [c['Key'] for c in contents]
    
    has_mp4 = any(k.endswith('.mp4') for k in keys)
    has_hls = any(k.endswith('.m3u8') or k.endswith('.ts') for k in keys)
    
    if has_mp4:
        mp4_done += 1
    elif has_hls:
        name = folder.rstrip('/').split('/')[-1]
        hls_only.append(name)
    
    if (i+1) % 50 == 0:
        print(f"   Checked {i+1}/{len(folders)}...")

print(f"\n📊 Results:")
print(f"   ✅ MP4 done: {mp4_done}")
print(f"   ❌ HLS only (belum convert): {len(hls_only)}")

if hls_only:
    print(f"\n📋 Drama yang BELUM di-convert ({len(hls_only)}):")
    for j, name in enumerate(hls_only, 1):
        print(f"   {j}. {name}")
