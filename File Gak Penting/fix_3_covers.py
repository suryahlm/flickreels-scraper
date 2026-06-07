"""Fix specific dramas that have segment covers instead of real covers"""
import boto3
import json
import requests

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

BUCKET = 'asiandrama-cdn'
SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

stream_base = "https://tender-connection-production-246f.up.railway.app/api/stream"

# The 3 problematic dramas
problem_dramas = [
    "Permainan Naik Pangkat (3826)",
    "Sekata dalam Diam (1859)",
    "Nenek Muda Kebangkitan Keluarga (1525)"
]

for folder_name in problem_dramas:
    print(f"=== {folder_name} ===")
    folder = f"flickreels/{folder_name}/"
    
    # Get metadata to find original API cover URL
    try:
        meta_obj = s3.get_object(Bucket=BUCKET, Key=f'{folder}metadata.json')
        metadata = json.loads(meta_obj['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f"  ❌ Metadata error: {e}")
        continue
    
    api_cover = metadata.get('cover', '')
    flickreels_id = metadata.get('id')
    
    print(f"  flickreels_id: {flickreels_id}")
    print(f"  Original API cover: {api_cover}")
    
    if not api_cover:
        print(f"  ❌ No API cover URL in metadata!")
        continue
    
    # Delete old cover files first
    cover_result = s3.list_objects_v2(Bucket=BUCKET, Prefix=f'{folder}cover')
    for obj in cover_result.get('Contents', []):
        print(f"  Deleting old: {obj['Key']}")
        s3.delete_object(Bucket=BUCKET, Key=obj['Key'])
    
    # Download fresh cover from API
    print(f"  Downloading from API...")
    try:
        resp = requests.get(api_cover, timeout=60)
        if resp.status_code != 200:
            print(f"  ❌ Download failed: {resp.status_code}")
            continue
        
        # Determine extension from URL
        ext = 'jpg'
        if '.png' in api_cover.lower():
            ext = 'png'
        elif '.webp' in api_cover.lower():
            ext = 'webp'
        
        # Upload to R2
        r2_key = f'{folder}cover.{ext}'
        s3.put_object(
            Bucket=BUCKET,
            Key=r2_key,
            Body=resp.content,
            ContentType=f'image/{ext}'
        )
        print(f"  ✅ Uploaded {len(resp.content)/1024:.1f}KB to {r2_key}")
        
        # Update metadata with correct cover_r2 path
        metadata['cover_r2'] = r2_key
        s3.put_object(
            Bucket=BUCKET,
            Key=f'{folder}metadata.json',
            Body=json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        print(f"  ✅ Metadata updated")
        
        # Update Supabase
        thumbnail_url = f"{stream_base}/{r2_key}"
        resp = requests.patch(
            f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{flickreels_id}',
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            },
            json={'thumbnail_url': thumbnail_url}
        )
        if resp.status_code in [200, 204]:
            print(f"  ✅ Supabase updated: {thumbnail_url}")
        else:
            print(f"  ❌ Supabase error: {resp.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()

print("Done!")
