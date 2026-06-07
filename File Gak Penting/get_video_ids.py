#!/usr/bin/env python3
"""Get all drama IDs with video content for app."""
import boto3
from botocore.config import Config
import re

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# List all folders
folders = []
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        folders.append(prefix['Prefix'])

print(f"Checking {len(folders)} folders...")

# Get all drama IDs with video content
video_ids = []

for folder in folders:
    folder_name = folder.replace('flickreels/', '').replace('/', '')
    if not folder_name or folder_name in ['dramas', 'test']:
        continue
    
    has_video = False
    
    # Check for episodes in EPISODES SUBDIRECTORY
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}episodes/', MaxKeys=10)
        contents = resp.get('Contents', [])
        ts_files = [c for c in contents if c['Key'].endswith('.ts')]
        if ts_files:
            has_video = True
    except:
        pass
    
    # Also check root level for ep_*.m3u8 (old format)
    if not has_video:
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}ep_', MaxKeys=5)
            if resp.get('Contents'):
                has_video = True
        except:
            pass
    
    if has_video:
        # Extract ID
        match = re.search(r'\((\d+)\)$', folder_name)
        if match:
            video_ids.append(match.group(1))

print(f"\nTotal dramas with video content: {len(video_ids)}")
print("\n// TypeScript Set for r2DramaService.ts:")
print("const WORKING_DRAMA_IDS = new Set([")

# Format as TypeScript
chunks = [video_ids[i:i+12] for i in range(0, len(video_ids), 12)]
for chunk in chunks:
    formatted = ', '.join([f"'{id}'" for id in chunk])
    print(f"    {formatted},")

print("]);")
