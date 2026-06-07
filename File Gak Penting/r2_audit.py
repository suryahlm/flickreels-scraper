#!/usr/bin/env python3
"""Complete R2 audit to understand what was scraped."""
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

# Categorize folders
complete = []  # Has cover + episodes
metadata_only = []  # Has metadata but no cover
empty = []  # No metadata

for folder in folders:
    folder_name = folder.replace('flickreels/', '').replace('/', '')
    if not folder_name or folder_name in ['dramas', 'test']:
        continue
    
    has_cover = False
    has_metadata = False
    has_episodes = False
    
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
    
    # Check for episodes
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}ep_', MaxKeys=1)
        if resp.get('Contents'):
            has_episodes = True
    except:
        pass
    
    # Categorize
    if has_cover and has_episodes:
        complete.append(folder_name)
    elif has_metadata and not has_cover:
        metadata_only.append(folder_name)
    else:
        empty.append(folder_name)

print(f"\nCOMPLETE (cover + episodes): {len(complete)}")
print(f"METADATA ONLY (no cover/episodes): {len(metadata_only)}")
print(f"EMPTY (no content): {len(empty)}")

print(f"\n--- Complete Dramas ({len(complete)}) ---")
for f in sorted(complete)[:20]:
    print(f"  - {f}")
if len(complete) > 20:
    print(f"  ... and {len(complete)-20} more")

print(f"\n--- Metadata Only ({len(metadata_only)}) ---")
for f in sorted(metadata_only)[:10]:
    print(f"  - {f}")
if len(metadata_only) > 10:
    print(f"  ... and {len(metadata_only)-10} more")
