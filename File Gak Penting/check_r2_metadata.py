#!/usr/bin/env python3
"""List R2 folders and check which ones have/don't have metadata.json"""

import boto3
from botocore.config import Config
import os

def main():
    # R2 credentials
    s3 = boto3.client('s3',
        endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
        aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
        aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
        config=Config(signature_version='s3v4')
    )

    bucket = 'asiandrama-cdn'
    
    # List all folders with pagination
    folders = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append(prefix['Prefix'])
    
    print(f"Total folders in R2: {len(folders)}")
    
    # Check metadata
    with_meta = []
    without_meta = []
    
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}metadata.json')
            with_meta.append(folder_name)
        except:
            without_meta.append(folder_name)
    
    print(f"\nWith metadata.json: {len(with_meta)}")
    print(f"WITHOUT metadata.json: {len(without_meta)}")
    
    if without_meta:
        print("\n=== Folders WITHOUT metadata.json ===")
        for f in sorted(without_meta):
            print(f"  - {f}")

if __name__ == "__main__":
    main()
