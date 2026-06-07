#!/usr/bin/env python3
"""Get list of incomplete drama IDs from R2 for re-scraping."""

import boto3
from botocore.config import Config
import re
import json

def main():
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
    
    # Find incomplete folders (no cover.jpg)
    incomplete_ids = []
    
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        if not folder_name or folder_name in ['dramas', 'test']:
            continue
        
        # Check if has cover.jpg
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}cover.jpg')
            continue  # Has cover, skip
        except:
            pass
        
        # Extract ID from folder name like "Title (1234)"
        match = re.search(r'\((\d+)\)$', folder_name)
        if match:
            drama_id = match.group(1)
            incomplete_ids.append(drama_id)
            print(f"  {drama_id}: {folder_name}")
    
    print(f"\n\nTotal incomplete drama IDs: {len(incomplete_ids)}")
    
    # Save to file
    with open('incomplete_drama_ids.json', 'w') as f:
        json.dump(incomplete_ids, f)
    
    print(f"\nSaved to incomplete_drama_ids.json")
    print(f"\nIDs for batch scraper:")
    print(','.join(incomplete_ids))

if __name__ == "__main__":
    main()
