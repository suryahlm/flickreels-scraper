#!/usr/bin/env python3
"""
Cover Completion v2 - Get cover URL from R2 metadata.json
Uses local metadata to find cover URLs, avoids external API calls
"""
import boto3
from botocore.config import Config
import requests
import re
import json

# R2 Client
s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# 52 strictly Indonesian drama IDs
INDONESIAN_IDS = set([
    '894', '4840', '5190', '5136', '4058', '3108', '5119', '2655', '3694', '721', '978', '5194',
    '5122', '487', '2491', '2343', '5071', '4009', '3495', '4255', '5137', '495', '977', '5235',
    '5202', '963', '5089', '4440', '3658', '5159', '3985', '4464', '4784', '533', '5135', '2186',
    '3674', '4187', '4158', '2518', '5220', '5031', '5247', '5099', '4511', '4839', '5043', '3164',
    '5226', '2691', '2858', '1445',
])

def get_dramas_missing_covers():
    """Find Indonesian dramas without cover.jpg"""
    folders = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append(prefix['Prefix'])
    
    missing = []
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        if not folder_name:
            continue
        
        match = re.search(r'\((\d+)\)$', folder_name)
        if not match or match.group(1) not in INDONESIAN_IDS:
            continue
        
        # Check if has cover
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}cover.jpg')
            continue  # Has cover
        except:
            pass
        
        missing.append({
            'id': match.group(1),
            'folder': folder,
            'folder_name': folder_name
        })
    
    return missing

def get_cover_from_metadata(folder):
    """Get cover URL from metadata.json in R2"""
    try:
        resp = s3.get_object(Bucket=bucket, Key=f'{folder}metadata.json')
        data = json.loads(resp['Body'].read().decode('utf-8'))
        return data.get('cover_url') or data.get('thumbnail_url')
    except:
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
    print("COVER COMPLETION v2 - FROM METADATA")
    print("=" * 60)
    
    missing = get_dramas_missing_covers()
    print(f"\nDramas missing covers: {len(missing)}")
    
    if not missing:
        print("All Indonesian dramas have covers!")
        return
    
    for d in missing:
        print(f"  - {d['folder_name']}")
    
    success = 0
    failed = 0
    
    print(f"\nProcessing...")
    for i, drama in enumerate(missing):
        print(f"[{i+1}/{len(missing)}] {drama['folder_name']}")
        
        # Get cover URL from metadata
        cover_url = get_cover_from_metadata(drama['folder'])
        if not cover_url:
            print(f"    ❌ No cover in metadata")
            failed += 1
            continue
        
        print(f"    Cover URL: {cover_url[:60]}...")
        
        if download_and_upload(drama['folder'], cover_url):
            print(f"    ✅ Uploaded")
            success += 1
        else:
            failed += 1
    
    print(f"\n✅ Done! Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
