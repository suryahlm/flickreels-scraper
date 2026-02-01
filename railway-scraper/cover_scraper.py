#!/usr/bin/env python3
"""
Cover Scraper for Railway - Downloads missing covers using FlickReels API
Deploy to Railway to bypass local DNS blocks
"""
import boto3
from botocore.config import Config
import requests
import time
import os

# R2 Config - from environment or defaults
R2_ACCOUNT_ID = os.environ.get('R2_ACCOUNT_ID', 'caa84fe6b1be065cda3836f0dac4b509')
R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY', 'a4903ea93c248388b6e295d6cdbc8617')
R2_SECRET_KEY = os.environ.get('R2_SECRET_KEY', '5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')
R2_BUCKET = os.environ.get('R2_BUCKET', 'asiandrama-cdn')

# FlickReels API
API_BASE = "https://api.flickreels.net"

HEADERS = {
    'User-Agent': 'okhttp/4.12.0',
    'Accept': 'application/json',
    'x-client-token': str(int(time.time() * 1000)),
    'x-client-ver': '22'
}

# 10 dramas missing covers with their folder names
MISSING_DRAMAS = [
    {'id': '4840', 'folder': 'flickreels/Aduh! Dukun Cilik Cari Cuan (4840)/'},
    {'id': '4058', 'folder': 'flickreels/Anak Lucu Hoki Datang (4058)/'},
    {'id': '2655', 'folder': 'flickreels/Bayang-Bayang Kehidupan (2655)/'},
    {'id': '3694', 'folder': 'flickreels/Bukan Bidakmu (3694)/'},
    {'id': '2491', 'folder': 'flickreels/Dimanja Tiga Menantu Setelah Cerai (2491)/'},
    {'id': '2343', 'folder': 'flickreels/Dokter Jenius Terlahir Kembali (2343)/'},
    {'id': '4255', 'folder': 'flickreels/Hidup Lagi, Kubalas dendam (4255)/'},
    {'id': '4440', 'folder': 'flickreels/Legenda Keluarga Japhar (4440)/'},
    {'id': '3658', 'folder': 'flickreels/Leluhur 10 Tahun\u200b\u200b (3658)/'},
    {'id': '2691', 'folder': 'flickreels/Surga di Telapak Kaki Ibu (2691)/'},
]

def get_s3_client():
    return boto3.client('s3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4')
    )

def get_cover_url(drama_id):
    """Get cover URL from FlickReels API"""
    try:
        url = f"{API_BASE}/app/playlet/detail"
        params = {'language_id': '6', 'playlet_id': drama_id}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        data = resp.json()
        
        if data.get('code') == 200:
            detail = data.get('data', {})
            return detail.get('cover_url') or detail.get('thumbnail_url')
    except Exception as e:
        print(f"  API error: {e}")
    return None

def download_and_upload(s3, folder, cover_url):
    """Download cover and upload to R2"""
    try:
        # Download
        resp = requests.get(cover_url, timeout=30)
        if resp.status_code != 200:
            print(f"  Download failed: {resp.status_code}")
            return False
        
        if len(resp.content) < 1000:
            print(f"  Image too small: {len(resp.content)} bytes")
            return False
        
        # Upload
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=f"{folder}cover.jpg",
            Body=resp.content,
            ContentType='image/jpeg'
        )
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("RAILWAY COVER SCRAPER")
    print("=" * 60)
    
    s3 = get_s3_client()
    success = 0
    failed = 0
    
    for drama in MISSING_DRAMAS:
        drama_id = drama['id']
        folder = drama['folder']
        
        print(f"\n[{drama_id}] {folder.split('/')[1]}")
        
        # Get cover URL
        cover_url = get_cover_url(drama_id)
        if not cover_url:
            print(f"  ❌ No cover URL")
            failed += 1
            continue
        
        print(f"  Cover: {cover_url[:50]}...")
        
        # Download and upload
        if download_and_upload(s3, folder, cover_url):
            print(f"  ✅ Uploaded!")
            success += 1
        else:
            failed += 1
        
        time.sleep(0.5)
    
    print(f"\n" + "=" * 60)
    print(f"DONE! Success: {success}, Failed: {failed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
