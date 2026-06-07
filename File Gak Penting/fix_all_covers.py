"""Fix cover URLs by downloading correct covers from API and re-uploading to R2"""
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

# List all drama folders
result = s3.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/')
folders = [p['Prefix'] for p in result.get('CommonPrefixes', [])]

print(f'Found {len(folders)} drama folders\n')

for folder in folders:
    folder_name = folder.replace('flickreels/', '').rstrip('/')
    print(f'=== {folder_name} ===')
    
    # Get metadata
    try:
        meta_obj = s3.get_object(Bucket=BUCKET, Key=f'{folder}metadata.json')
        metadata = json.loads(meta_obj['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f'  ❌ Metadata error: {e}')
        continue
    
    # Get cover URL from API metadata
    api_cover = metadata.get('cover', '')
    if not api_cover:
        print(f'  ❌ No cover URL in metadata')
        continue
    
    print(f'  API cover: {api_cover[:60]}...')
    
    # Download cover from API
    try:
        resp = requests.get(api_cover, timeout=30)
        if resp.status_code != 200:
            print(f'  ❌ Download failed: {resp.status_code}')
            continue
        
        # Determine extension
        ext = 'jpg'
        if 'png' in api_cover.lower():
            ext = 'png'
        elif 'webp' in api_cover.lower():
            ext = 'webp'
        
        # Upload to correct location
        r2_key = f'{folder}cover.{ext}'
        s3.put_object(
            Bucket=BUCKET,
            Key=r2_key,
            Body=resp.content,
            ContentType=f'image/{ext}'
        )
        print(f'  ✅ Uploaded to {r2_key}')
        
        # Update metadata with correct cover_r2 path
        metadata['cover_r2'] = r2_key.rstrip('/')
        s3.put_object(
            Bucket=BUCKET,
            Key=f'{folder}metadata.json',
            Body=json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        print(f'  ✅ Updated metadata')
        
        # Update Supabase with correct thumbnail URL
        flickreels_id = metadata.get('id')
        if flickreels_id:
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
                print(f'  ✅ Supabase updated')
            else:
                print(f'  ❌ Supabase error: {resp.status_code}')
        
    except Exception as e:
        print(f'  ❌ Error: {e}')
    
    print()

print('Done!')
