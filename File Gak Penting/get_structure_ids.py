#!/usr/bin/env python3
"""Get drama IDs by episode structure format."""
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

# Categorize by episode structure
root_level_ids = []  # ep_*.m3u8 at root
subdir_level_ids = []  # episodes/ep_*.m3u8

for folder in folders:
    folder_name = folder.replace('flickreels/', '').replace('/', '')
    if not folder_name or folder_name in ['dramas', 'test']:
        continue
    
    drama_id = None
    match = re.search(r'\((\d+)\)$', folder_name)
    if match:
        drama_id = match.group(1)
    else:
        continue
    
    # Check for root level ep_*.m3u8
    has_root = False
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}ep_', MaxKeys=3)
        if resp.get('Contents'):
            has_root = True
    except:
        pass
    
    # Check for episodes/ep_*.m3u8
    has_subdir = False
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}episodes/ep_', MaxKeys=3)
        if resp.get('Contents'):
            has_subdir = True
    except:
        pass
    
    if has_root:
        root_level_ids.append(drama_id)
    elif has_subdir:
        subdir_level_ids.append(drama_id)

print(f"\nROOT LEVEL (ep_*.m3u8): {len(root_level_ids)}")
print(f"SUBDIR LEVEL (episodes/ep_*.m3u8): {len(subdir_level_ids)}")

print("\n// TypeScript Set for ROOT_LEVEL_DRAMA_IDS:")
print("const ROOT_LEVEL_DRAMA_IDS = new Set([")
chunks = [root_level_ids[i:i+12] for i in range(0, len(root_level_ids), 12)]
for chunk in chunks:
    formatted = ', '.join([f"'{id}'" for id in chunk])
    print(f"    {formatted},")
print("]);")
