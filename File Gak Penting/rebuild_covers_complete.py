"""Complete rebuild of all cover URLs - fix once and for all"""
import requests
import boto3
import json
import re

SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

BUCKET = 'asiandrama-cdn'
stream_base = "https://tender-connection-production-246f.up.railway.app/api/stream"

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("=== COMPLETE REBUILD OF COVER URLS ===\n")

# Get all drama folders from R2
result = s3.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/')

for prefix in result.get('CommonPrefixes', []):
    folder = prefix['Prefix']  # e.g., "flickreels/CEO itu Ayah Anakku (1675)/"
    folder_name = folder.replace('flickreels/', '').rstrip('/')  # e.g., "CEO itu Ayah Anakku (1675)"
    
    # Extract flickreels_id from folder name using regex
    match = re.search(r'\((\d+)\)$', folder_name)
    if not match:
        print(f"❌ Cannot extract ID from: {folder_name}")
        continue
    
    flickreels_id = match.group(1)
    drama_title = folder_name.rsplit(' (', 1)[0]  # Get title part
    
    print(f"Drama: {drama_title} (ID: {flickreels_id})")
    
    # Find cover file in R2 (prefer jpg, then png)
    cover_result = s3.list_objects_v2(Bucket=BUCKET, Prefix=f'{folder}cover')
    cover_files = [o['Key'] for o in cover_result.get('Contents', [])]
    
    if not cover_files:
        print(f"  ❌ No cover file found in R2")
        continue
    
    # Get the first cover file (should be the correct one now)
    # Prefer the newest/largest file
    best_cover = None
    best_size = 0
    for cf in cover_files:
        obj = s3.head_object(Bucket=BUCKET, Key=cf)
        if obj['ContentLength'] > best_size:
            best_size = obj['ContentLength']
            best_cover = cf
    
    if not best_cover:
        print(f"  ❌ No valid cover file")
        continue
    
    # Build correct thumbnail URL
    cover_filename = best_cover.split('/')[-1]  # e.g., "cover.png"
    correct_url = f"{stream_base}/flickreels/{folder_name}/{cover_filename}"
    
    print(f"  R2 cover: {best_cover}")
    print(f"  New URL: {correct_url}")
    
    # Update Supabase with correct URL
    resp = requests.patch(
        f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{flickreels_id}',
        headers=headers,
        json={'thumbnail_url': correct_url}
    )
    
    if resp.status_code in [200, 204]:
        print(f"  ✅ Supabase updated")
    else:
        print(f"  ❌ Supabase error: {resp.status_code} - {resp.text}")
    
    print()

print("\n=== VERIFICATION ===\n")

# Verify all dramas have correct URLs
resp = requests.get(
    f'{SUPABASE_URL}/rest/v1/dramas?select=title,flickreels_id,thumbnail_url',
    headers={'apikey': SUPABASE_KEY}
)

for d in resp.json():
    thumb = d.get('thumbnail_url', '')
    fid = d['flickreels_id']
    
    # Check if URL contains the correct flickreels_id
    if f'({fid})' in thumb:
        print(f"✅ {d['title'][:30]} -> correct")
    else:
        print(f"❌ {d['title'][:30]} -> WRONG! URL: {thumb[:60]}...")

print("\nDone!")
