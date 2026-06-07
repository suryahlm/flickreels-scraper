#!/usr/bin/env python3
"""
Cover Completion v3 - Use Railway API for cover URLs
Railway API has cover_url for each drama
"""
import boto3
from botocore.config import Config
import requests
import re

# R2 Client
s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# 10 dramas missing covers
MISSING_IDS = ['4840', '4058', '2655', '3694', '2491', '2343', '4255', '4440', '3658', '2691']

# Railway Admin API
RAILWAY_API = "https://tender-connection-production-246f.up.railway.app/api/r2-dramas"

def get_dramas_from_railway():
    """Get all dramas from Railway API"""
    print("Fetching from Railway API...")
    resp = requests.get(RAILWAY_API, timeout=60)
    data = resp.json()
    dramas = data.get('dramas', [])
    print(f"Got {len(dramas)} dramas from API")
    
    # Create lookup by ID
    lookup = {}
    for d in dramas:
        drama_id = str(d.get('id', ''))
        if drama_id:
            lookup[drama_id] = d
    return lookup

def get_r2_folder(drama_id):
    """Find the folder name for a drama ID in R2"""
    folders = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folder_name = prefix['Prefix'].replace('flickreels/', '').replace('/', '')
            if folder_name and f'({drama_id})' in folder_name:
                return prefix['Prefix']
    return None

def download_and_upload(folder, cover_url):
    """Download and upload cover"""
    try:
        resp = requests.get(cover_url, timeout=30)
        if resp.status_code != 200:
            return False
        
        s3.put_object(
            Bucket=bucket,
            Key=f'{folder}cover.jpg',
            Body=resp.content,
            ContentType='image/jpeg'
        )
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def main():
    print("=" * 60)
    print("COVER COMPLETION v3 - VIA RAILWAY API")
    print("=" * 60)
    
    # Get drama data from Railway
    dramas = get_dramas_from_railway()
    
    success = 0
    failed = 0
    
    for drama_id in MISSING_IDS:
        print(f"\n[{drama_id}]")
        
        # Get drama info
        drama = dramas.get(drama_id)
        if not drama:
            print(f"  ❌ Not found in API")
            failed += 1
            continue
        
        cover_url = drama.get('cover_url', '')
        if not cover_url:
            print(f"  ❌ No cover_url in API")
            failed += 1
            continue
        
        print(f"  Title: {drama.get('title', 'Unknown')}")
        print(f"  Cover: {cover_url[:50]}...")
        
        # Find R2 folder
        folder = get_r2_folder(drama_id)
        if not folder:
            print(f"  ❌ Folder not found in R2")
            failed += 1
            continue
        
        print(f"  Folder: {folder}")
        
        # Download and upload
        if download_and_upload(folder, cover_url):
            print(f"  ✅ Uploaded!")
            success += 1
        else:
            print(f"  ❌ Upload failed")
            failed += 1
    
    print(f"\n" + "=" * 60)
    print(f"DONE! Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
