#!/usr/bin/env python3
"""Check all R2 folders for missing covers and content."""

import boto3
from botocore.config import Config

def main():
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
    print("=" * 60)
    
    # Check each folder for required files
    has_cover = []
    no_cover = []
    has_metadata = []
    no_metadata = []
    has_episodes = []
    no_episodes = []
    
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        if not folder_name or folder_name in ['dramas', 'test']:
            continue
            
        # Check cover.jpg
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}cover.jpg')
            has_cover.append(folder_name)
        except:
            no_cover.append(folder_name)
        
        # Check metadata.json
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}metadata.json')
            has_metadata.append(folder_name)
        except:
            no_metadata.append(folder_name)
        
        # Check if has any ep_*.m3u8 files
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}ep_', MaxKeys=1)
            if resp.get('Contents'):
                has_episodes.append(folder_name)
            else:
                no_episodes.append(folder_name)
        except:
            no_episodes.append(folder_name)
    
    print(f"\n📊 SUMMARY:")
    print(f"  Folders with cover.jpg:    {len(has_cover)}")
    print(f"  Folders WITHOUT cover.jpg: {len(no_cover)}")
    print(f"  Folders with metadata:     {len(has_metadata)}")
    print(f"  Folders WITHOUT metadata:  {len(no_metadata)}")
    print(f"  Folders with episodes:     {len(has_episodes)}")
    print(f"  Folders WITHOUT episodes:  {len(no_episodes)}")
    
    if no_cover:
        print(f"\n❌ FOLDERS WITHOUT cover.jpg ({len(no_cover)}):")
        for f in sorted(no_cover)[:50]:  # Show first 50
            print(f"  - {f}")
        if len(no_cover) > 50:
            print(f"  ... and {len(no_cover) - 50} more")
    
    if no_metadata:
        print(f"\n❌ FOLDERS WITHOUT metadata.json ({len(no_metadata)}):")
        for f in sorted(no_metadata):
            print(f"  - {f}")
    
    if no_episodes:
        print(f"\n❌ FOLDERS WITHOUT episodes ({len(no_episodes)}):")
        for f in sorted(no_episodes)[:20]:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
