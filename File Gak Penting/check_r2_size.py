#!/usr/bin/env python3
"""Check actual R2 storage usage"""
import boto3
from botocore.config import Config

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# Check all top-level prefixes
print('=== ALL TOP-LEVEL PREFIXES ===')
resp = s3.list_objects_v2(Bucket=bucket, Delimiter='/', MaxKeys=100)
for prefix in resp.get('CommonPrefixes', []):
    p = prefix['Prefix']
    print(f'  {p}')

# Count objects and size in flickreels/
print()
print('=== FLICKREELS FOLDER STATS ===')
total_size = 0
total_objects = 0
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/'):
    for obj in page.get('Contents', []):
        total_objects += 1
        total_size += obj.get('Size', 0)

print(f'Total objects in flickreels/: {total_objects:,}')
print(f'Total size: {total_size / (1024**3):.2f} GB')

# Check for other folders at root
print()
print('=== CHECKING OTHER FOLDERS ===')
for prefix in resp.get('CommonPrefixes', []):
    p = prefix['Prefix']
    if p != 'flickreels/':
        folder_size = 0
        folder_objects = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=p):
            for obj in page.get('Contents', []):
                folder_objects += 1
                folder_size += obj.get('Size', 0)
        print(f'{p}: {folder_objects:,} objects, {folder_size / (1024**3):.2f} GB')
