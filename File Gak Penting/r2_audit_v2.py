#!/usr/bin/env python3
"""Correct R2 audit - check episodes subdirectory structure."""
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

print(f"Total folders in R2: {len(folders)}")
print("="*60)

# Categorize folders correctly
complete = []  # Has cover + episodes/*.ts files
has_episodes = []  # Has episodes but no cover
has_cover_only = []  # Has cover but no episodes
metadata_only = []  # Only metadata

for folder in folders:
    folder_name = folder.replace('flickreels/', '').replace('/', '')
    if not folder_name or folder_name in ['dramas', 'test']:
        continue
    
    has_cover = False
    has_metadata = False
    has_video = False
    episode_count = 0
    
    # Check cover.jpg
    try:
        s3.head_object(Bucket=bucket, Key=f'{folder}cover.jpg')
        has_cover = True
    except:
        pass
    
    # Check metadata.json
    try:
        s3.head_object(Bucket=bucket, Key=f'{folder}metadata.json')
        has_metadata = True
    except:
        pass
    
    # Check for episodes in EPISODES SUBDIRECTORY (correct path!)
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}episodes/', MaxKeys=100)
        contents = resp.get('Contents', [])
        # Count .m3u8 files (each = 1 episode)
        m3u8_files = [c for c in contents if c['Key'].endswith('.m3u8')]
        episode_count = len(m3u8_files)
        # Check for .ts video files
        ts_files = [c for c in contents if c['Key'].endswith('.ts')]
        if ts_files:
            has_video = True
    except:
        pass
    
    # Also check root level for ep_*.m3u8 (old format)
    if not has_video:
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}ep_', MaxKeys=10)
            if resp.get('Contents'):
                has_video = True
                episode_count = len([c for c in resp.get('Contents', []) if c['Key'].endswith('.m3u8')])
        except:
            pass
    
    # Categorize
    if has_cover and has_video:
        complete.append((folder_name, episode_count))
    elif has_video and not has_cover:
        has_episodes.append((folder_name, episode_count))
    elif has_cover and not has_video:
        has_cover_only.append(folder_name)
    elif has_metadata:
        metadata_only.append(folder_name)

print(f"\nCOMPLETE (cover + episodes): {len(complete)}")
print(f"HAS EPISODES (no cover): {len(has_episodes)}")
print(f"HAS COVER ONLY: {len(has_cover_only)}")
print(f"METADATA ONLY: {len(metadata_only)}")

total_with_content = len(complete) + len(has_episodes)
print(f"\n>>> TOTAL WITH VIDEO CONTENT: {total_with_content}")

print(f"\n--- Complete Dramas ({len(complete)}) ---")
for f, ep in sorted(complete, key=lambda x: x[0])[:15]:
    print(f"  - {f} ({ep} eps)")
if len(complete) > 15:
    print(f"  ... and {len(complete)-15} more")

print(f"\n--- Has Episodes but No Cover ({len(has_episodes)}) ---")
for f, ep in sorted(has_episodes, key=lambda x: x[0])[:15]:
    print(f"  - {f} ({ep} eps)")
if len(has_episodes) > 15:
    print(f"  ... and {len(has_episodes)-15} more")
