#!/usr/bin/env python3
"""
Cover Completion v4 - Get original cover URLs from FlickReels CDN
Uses cached headers from previous successful downloads
"""
import boto3
from botocore.config import Config
import requests
import re
import time

# R2 Client
s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# FlickReels API - try alternative domains
API_DOMAINS = [
    "https://api.flickreels.net",
    "https://api-vn.flickreels.net",
    "https://api-us.flickreels.net",
]

HEADERS = {
    'User-Agent': 'okhttp/4.12.0',
    'Accept': 'application/json',
    'x-client-token': '1738425606266',
    'x-client-ver': '22'
}

# 10 dramas missing covers
MISSING = [
    ('4840', 'Aduh! Dukun Cilik Cari Cuan'),
    ('4058', 'Anak Lucu Hoki Datang'),
    ('2655', 'Bayang-Bayang Kehidupan'),
    ('3694', 'Bukan Bidakmu'),
    ('2491', 'Dimanja Tiga Menantu Setelah Cerai'),
    ('2343', 'Dokter Jenius Terlahir Kembali'),
    ('4255', 'Hidup Lagi, Kubalas dendam'),
    ('4440', 'Legenda Keluarga Japhar'),
    ('3658', 'Leluhur 10 Tahun'),
    ('2691', 'Surga di Telapak Kaki Ibu'),
]

def get_cover_from_api(drama_id):
    """Try to get cover URL from FlickReels API"""
    for domain in API_DOMAINS:
        try:
            url = f"{domain}/app/playlet/detail"
            params = {'language_id': '6', 'playlet_id': drama_id}
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            data = resp.json()
            
            if data.get('code') == 200:
                detail = data.get('data', {})
                cover = detail.get('cover_url') or detail.get('thumbnail_url')
                if cover:
                    return cover
        except Exception as e:
            print(f"    {domain}: {e}")
            continue
    return None

def find_r2_folder(drama_id):
    """Find folder in R2 for drama ID"""
    folders = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            if f'({drama_id})' in prefix['Prefix']:
                return prefix['Prefix']
    return None

def upload_cover(folder, image_data):
    """Upload cover to R2"""
    try:
        s3.put_object(
            Bucket=bucket,
            Key=f'{folder}cover.jpg',
            Body=image_data,
            ContentType='image/jpeg'
        )
        return True
    except Exception as e:
        print(f"    Upload error: {e}")
        return False

def main():
    print("=" * 60)
    print("COVER COMPLETION v4 - DIRECT FLICKREELS CDN")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    for drama_id, title in MISSING:
        print(f"\n[{drama_id}] {title}")
        
        # Find R2 folder
        folder = find_r2_folder(drama_id)
        if not folder:
            print(f"  ❌ No folder in R2")
            failed += 1
            continue
        
        # Try to get cover from FlickReels API
        print(f"  Getting cover from FlickReels...")
        cover_url = get_cover_from_api(drama_id)
        
        if not cover_url:
            print(f"  ❌ No cover URL from API")
            failed += 1
            continue
        
        print(f"  Cover: {cover_url[:60]}...")
        
        # Download image
        try:
            resp = requests.get(cover_url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 1000:
                if upload_cover(folder, resp.content):
                    print(f"  ✅ Uploaded!")
                    success += 1
                else:
                    failed += 1
            else:
                print(f"  ❌ Download failed: status={resp.status_code}, size={len(resp.content)}")
                failed += 1
        except Exception as e:
            print(f"  ❌ Download error: {e}")
            failed += 1
        
        time.sleep(0.5)
    
    print(f"\n" + "=" * 60)
    print(f"DONE! Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
