#!/usr/bin/env python3
"""
Cover Completion v5 - Try multiple CDN URL patterns
FlickReels uses various CDN patterns for covers
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

# CDN URL patterns to try (based on working cover URLs)
CDN_PATTERNS = [
    "https://cdn-image.flickreels.net/cover/{id}.jpg",
    "https://cdn.flickreels.net/cover/{id}.jpg",
    "https://image.flickreels.net/cover/{id}.jpg",
    "https://cdn-image.flickreels.net/playlet/cover/{id}.jpg",
    "https://cdn.flickreels.net/playlet/{id}/cover.jpg",
    "https://static.flickreels.net/cover/{id}.jpg",
]

# 10 dramas missing covers
MISSING = [
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

def try_download_cover(drama_id):
    """Try multiple CDN patterns to download cover"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for pattern in CDN_PATTERNS:
        url = pattern.format(id=drama_id)
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content, url
        except:
            pass
    return None, None

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
    print("COVER COMPLETION v5 - CDN PATTERNS")
    print("=" * 60)
    
    success = 0
    failed = 0
    
    for drama in MISSING:
        drama_id = drama['id']
        folder = drama['folder']
        title = folder.split('/')[1].rsplit(' (', 1)[0]
        
        print(f"\n[{drama_id}] {title}")
        
        # Try CDN patterns
        print(f"  Trying CDN patterns...")
        image_data, found_url = try_download_cover(drama_id)
        
        if image_data:
            print(f"  ✅ Found: {found_url}")
            if upload_cover(folder, image_data):
                print(f"  ✅ Uploaded!")
                success += 1
            else:
                failed += 1
        else:
            print(f"  ❌ No CDN pattern worked")
            failed += 1
        
        time.sleep(0.3)
    
    print(f"\n" + "=" * 60)
    print(f"DONE! Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
