#!/usr/bin/env python3
"""Get list of drama IDs that have cover.jpg in R2."""
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

print(f"Total folders: {len(folders)}")

# Find folders WITH cover.jpg
working_ids = []
for folder in folders:
    folder_name = folder.replace('flickreels/', '').replace('/', '')
    if not folder_name or folder_name in ['dramas', 'test']:
        continue
    
    # Check cover.jpg
    try:
        s3.head_object(Bucket=bucket, Key=f'{folder}cover.jpg')
        # Extract ID
        match = re.search(r'\((\d+)\)$', folder_name)
        if match:
            working_ids.append(match.group(1))
    except:
        pass

print(f"Folders with cover.jpg: {len(working_ids)}")
print("\n// TypeScript Set for r2DramaService.ts:")
print("const WORKING_DRAMA_IDS = new Set([")

# Format as TypeScript
chunks = [working_ids[i:i+12] for i in range(0, len(working_ids), 12)]
for chunk in chunks:
    formatted = ', '.join([f"'{id}'" for id in chunk])
    print(f"    {formatted},")

print("]);")
