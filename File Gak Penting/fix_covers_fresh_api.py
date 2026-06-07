"""Fix covers by fetching FRESH data from the original API"""
import requests
import boto3
import json

# The 4 problematic dramas with their IDs
PROBLEM_DRAMAS = [
    {"id": "1859", "title": "Sekata dalam Diam"},
    {"id": "533", "title": "Menikah lagi dengan Ketua Direksi(Dubbing)"},
    {"id": "3826", "title": "Permainan Naik Pangkat"},
    {"id": "1525", "title": "Nenek Muda Kebangkitan Keluarga"},
]

# API to get drama details
API_BASE = "https://m-api2.iyf.tv/api/list/drama/detail"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Accept-Language": "id",
    "referer": "https://m2.iyf.tv/",
    "origin": "https://m2.iyf.tv"
}

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

BUCKET = 'asiandrama-cdn'
SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

stream_base = "https://tender-connection-production-246f.up.railway.app/api/stream"

for drama in PROBLEM_DRAMAS:
    drama_id = drama["id"]
    title = drama["title"]
    
    print(f"\n=== {title} (ID: {drama_id}) ===")
    
    # Fetch fresh data from API
    print(f"  Fetching from API...")
    try:
        resp = requests.get(
            f"{API_BASE}?id={drama_id}&source_key=iyf",
            headers=HEADERS,
            timeout=30
        )
        
        if resp.status_code != 200:
            print(f"  ❌ API error: {resp.status_code}")
            continue
            
        data = resp.json()
        if data.get("code") != 200:
            print(f"  ❌ API returned error: {data}")
            continue
        
        drama_data = data.get("data", {})
        fresh_cover = drama_data.get("cover", "")
        
        print(f"  Fresh cover URL: {fresh_cover[:70]}...")
        
        if not fresh_cover:
            print(f"  ❌ No cover URL from API!")
            continue
        
        # Download fresh cover
        print(f"  Downloading fresh cover...")
        cover_resp = requests.get(fresh_cover, timeout=60)
        
        if cover_resp.status_code != 200:
            print(f"  ❌ Cover download failed: {cover_resp.status_code}")
            continue
        
        print(f"  Downloaded {len(cover_resp.content)/1024:.1f}KB")
        
        # Find R2 folder for this drama
        result = s3.list_objects_v2(Bucket=BUCKET, Prefix=f'flickreels/', Delimiter='/')
        folder = None
        for p in result.get('CommonPrefixes', []):
            if f'({drama_id})' in p['Prefix']:
                folder = p['Prefix']
                break
        
        if not folder:
            print(f"  ❌ R2 folder not found!")
            continue
        
        folder_name = folder.replace('flickreels/', '').rstrip('/')
        print(f"  R2 folder: {folder_name}")
        
        # Delete old cover files
        cover_result = s3.list_objects_v2(Bucket=BUCKET, Prefix=f'{folder}cover')
        for obj in cover_result.get('Contents', []):
            print(f"  Deleting: {obj['Key'].split('/')[-1]}")
            s3.delete_object(Bucket=BUCKET, Key=obj['Key'])
        
        # Determine extension
        ext = 'jpg'
        if '.png' in fresh_cover.lower():
            ext = 'png'
        elif '.webp' in fresh_cover.lower():
            ext = 'webp'
        
        # Upload fresh cover
        r2_key = f'{folder}cover.{ext}'
        s3.put_object(
            Bucket=BUCKET,
            Key=r2_key,
            Body=cover_resp.content,
            ContentType=f'image/{ext}'
        )
        print(f"  ✅ Uploaded to {r2_key}")
        
        # Update metadata in R2
        try:
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
            print(f"  ✅ Metadata updated")
        except Exception as e:
            print(f"  ⚠️ Metadata update failed: {e}")
        
        # Update Supabase
        thumbnail_url = f"{stream_base}/{r2_key}"
        resp = requests.patch(
            f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{drama_id}',
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            },
            json={'thumbnail_url': thumbnail_url}
        )
        if resp.status_code in [200, 204]:
            print(f"  ✅ Supabase updated")
        else:
            print(f"  ❌ Supabase error: {resp.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n\nDone! Refresh the app to see correct covers.")
