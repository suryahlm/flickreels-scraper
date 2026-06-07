#!/usr/bin/env python3
"""
Cover Completion Script - Download missing cover.jpg for Indonesian dramas
Uses FlickReels API to get cover images and upload directly to R2
"""
import boto3
from botocore.config import Config
import requests
import re
import json
import time

# R2 Client
s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# FlickReels API
API_BASE = "https://api-vn.flickreels.net"
HEADERS = {
    'User-Agent': 'okhttp/4.12.0',
    'Accept': 'application/json',
    'x-client-token': '1738425606266',
    'x-client-ver': '22'
}

# 52 strictly Indonesian drama IDs
INDONESIAN_IDS = [
    '894', '4840', '5190', '5136', '4058', '3108', '5119', '2655', '3694', '721', '978', '5194',
    '5122', '487', '2491', '2343', '5071', '4009', '3495', '4255', '5137', '495', '977', '5235',
    '5202', '963', '5089', '4440', '3658', '5159', '3985', '4464', '4784', '533', '5135', '2186',
    '3674', '4187', '4158', '2518', '5220', '5031', '5247', '5099', '4511', '4839', '5043', '3164',
    '5226', '2691', '2858', '1445',
]

def get_drama_folders():
    """Get all Indonesian drama folders and check if they have cover.jpg"""
    folders = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append(prefix['Prefix'])
    
    # Filter to Indonesian dramas and check for covers
    results = []
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        if not folder_name:
            continue
        
        match = re.search(r'\((\d+)\)$', folder_name)
        if not match:
            continue
        
        drama_id = match.group(1)
        if drama_id not in INDONESIAN_IDS:
            continue
        
        # Check if has cover.jpg
        has_cover = False
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}cover.jpg')
            has_cover = True
        except:
            pass
        
        results.append({
            'id': drama_id,
            'folder': folder,
            'folder_name': folder_name,
            'has_cover': has_cover
        })
    
    return results

def get_cover_url(drama_id):
    """Get cover URL from FlickReels API"""
    try:
        # Get drama details
        url = f"{API_BASE}/app/playlet/detail"
        params = {
            'language_id': '6',  # Indonesian
            'playlet_id': drama_id
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()
        
        if data.get('code') == 200:
            detail = data.get('data', {})
            cover_url = detail.get('cover_url') or detail.get('thumbnail_url')
            return cover_url
        return None
    except Exception as e:
        print(f"    Error getting cover URL: {e}")
        return None

def download_and_upload_cover(drama_id, folder, cover_url):
    """Download cover from URL and upload to R2"""
    try:
        # Download image
        resp = requests.get(cover_url, timeout=30)
        if resp.status_code != 200:
            return False
        
        image_data = resp.content
        content_type = resp.headers.get('Content-Type', 'image/jpeg')
        
        # Upload to R2
        key = f"{folder}cover.jpg"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=image_data,
            ContentType=content_type
        )
        return True
    except Exception as e:
        print(f"    Error uploading cover: {e}")
        return False

def main():
    print("=" * 60)
    print("COVER COMPLETION - DOWNLOAD MISSING COVERS")
    print("=" * 60)
    
    # Get drama folders
    dramas = get_drama_folders()
    print(f"\nTotal Indonesian dramas in R2: {len(dramas)}")
    
    with_cover = [d for d in dramas if d['has_cover']]
    without_cover = [d for d in dramas if not d['has_cover']]
    
    print(f"With cover: {len(with_cover)}")
    print(f"Without cover: {len(without_cover)}")
    
    if not without_cover:
        print("\n✅ All Indonesian dramas have covers!")
        return
    
    print(f"\n--- DRAMAS MISSING COVERS ({len(without_cover)}) ---")
    for d in without_cover[:10]:
        print(f"  {d['id']}: {d['folder_name']}")
    if len(without_cover) > 10:
        print(f"  ... and {len(without_cover) - 10} more")
    
    print(f"\nDownloading covers...")
    success = 0
    failed = 0
    
    for i, drama in enumerate(without_cover):
        drama_id = drama['id']
        folder = drama['folder']
        
        print(f"[{i+1}/{len(without_cover)}] {drama['folder_name']}")
        
        # Get cover URL from API
        cover_url = get_cover_url(drama_id)
        if not cover_url:
            print(f"    ❌ No cover URL found")
            failed += 1
            continue
        
        # Download and upload
        if download_and_upload_cover(drama_id, folder, cover_url):
            print(f"    ✅ Cover uploaded")
            success += 1
        else:
            print(f"    ❌ Failed to upload")
            failed += 1
        
        time.sleep(0.3)  # Rate limit
    
    print(f"\n" + "=" * 60)
    print(f"COVER COMPLETION DONE!")
    print(f"=" * 60)
    print(f"Success: {success}")
    print(f"Failed: {failed}")

if __name__ == "__main__":
    main()
