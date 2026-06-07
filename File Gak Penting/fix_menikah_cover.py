"""Fix Menikah lagi dengan Ketua Direksi cover"""
import sys
sys.path.insert(0, "D:\\Surya\\IT\\Test Scraping\\FlickReels\\railway-scraper")

from batch_scraper_indonesia import IndonesianAPI
import requests
import boto3
import json

api = IndonesianAPI()

drama_id = "533"
title = "Menikah lagi dengan Ketua Direksi(Dubbing)"

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

BUCKET = 'asiandrama-cdn'
SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

stream_base = "https://tender-connection-production-246f.up.railway.app/api/stream"

print(f"=== {title} (ID: {drama_id}) ===")

# Fetch drama detail from API
print(f"Fetching from API...")
detail = api.get_drama_detail(drama_id)

if not detail:
    print(f"❌ Could not get detail from API")
    exit(1)

print(f"Detail: {detail}")
fresh_cover = detail.get("cover", "")
print(f"Fresh cover URL: {fresh_cover}")

if not fresh_cover:
    print("❌ No cover URL from API")
    exit(1)

# Download fresh cover
print(f"Downloading fresh cover...")
cover_resp = requests.get(fresh_cover, timeout=60)

if cover_resp.status_code != 200:
    print(f"❌ Cover download failed: {cover_resp.status_code}")
    exit(1)

print(f"Downloaded {len(cover_resp.content)/1024:.1f}KB")

# Find R2 folder
folder = "flickreels/Menikah lagi dengan Ketua Direksi(Dubbing) (533)/"
folder_name = "Menikah lagi dengan Ketua Direksi(Dubbing) (533)"

# Delete ALL old cover files
print("Deleting old covers...")
cover_result = s3.list_objects_v2(Bucket=BUCKET, Prefix=f'{folder}cover')
for obj in cover_result.get('Contents', []):
    print(f"  Deleting: {obj['Key']}")
    s3.delete_object(Bucket=BUCKET, Key=obj['Key'])

# Determine extension
ext = 'jpg'
if '.png' in fresh_cover.lower():
    ext = 'png'
elif '.webp' in fresh_cover.lower():
    ext = 'webp'

print(f"Extension: {ext}")

# Upload fresh cover
r2_key = f'{folder}cover.{ext}'
s3.put_object(
    Bucket=BUCKET,
    Key=r2_key,
    Body=cover_resp.content,
    ContentType=f'image/{ext}'
)
print(f"✅ Uploaded to {r2_key}")

# Update metadata
meta_obj = s3.get_object(Bucket=BUCKET, Key=f'{folder}metadata.json')
metadata = json.loads(meta_obj['Body'].read().decode('utf-8'))
metadata['cover'] = fresh_cover
metadata['cover_r2'] = r2_key
s3.put_object(
    Bucket=BUCKET,
    Key=f'{folder}metadata.json',
    Body=json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8'),
    ContentType='application/json'
)
print(f"✅ Metadata updated")

# Update Supabase
thumbnail_url = f"{stream_base}/{r2_key}"
print(f"Updating Supabase with: {thumbnail_url}")

resp = requests.patch(
    f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{drama_id}',
    headers={
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    },
    json={'thumbnail_url': thumbnail_url}
)
print(f"Supabase response: {resp.status_code}")

if resp.status_code in [200, 204]:
    print(f"✅ Supabase updated!")
else:
    print(f"❌ Supabase error: {resp.text}")

print("\nDone! Kill app and refresh.")
