"""Deep check: verify Supabase URLs and R2 content"""
import requests
import boto3

SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

# Get all dramas from Supabase
resp = requests.get(
    f'{SUPABASE_URL}/rest/v1/dramas?select=id,title,flickreels_id,thumbnail_url',
    headers={'apikey': SUPABASE_KEY}
)

print("=== SUPABASE DRAMAS ===\n")
for d in resp.json():
    print(f"Title: {d['title']}")
    print(f"  flickreels_id: {d['flickreels_id']}")
    print(f"  thumbnail_url: {d.get('thumbnail_url', 'NONE')}")
    
    # Check if thumbnail URL points to correct folder
    thumb = d.get('thumbnail_url', '')
    if thumb:
        # Extract folder name from URL
        # URL format: https://.../api/stream/flickreels/{folder}/cover.ext
        if '/flickreels/' in thumb:
            folder_part = thumb.split('/flickreels/')[-1]
            folder_name = folder_part.rsplit('/cover', 1)[0] if '/cover' in folder_part else folder_part
            
            # Check if drama title is in folder name
            title_clean = d['title'].replace(':', '').replace('?', '')
            if title_clean in folder_name or d['flickreels_id'] in folder_name:
                print(f"  ✅ URL looks correct")
            else:
                print(f"  ❌ URL MISMATCH! Folder: {folder_name}")
    print()

print("\n=== R2 COVER FILES ===\n")

# Check actual R2 cover files
result = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix='flickreels/', Delimiter='/')
for prefix in result.get('CommonPrefixes', []):
    folder = prefix['Prefix']
    folder_name = folder.replace('flickreels/', '').rstrip('/')
    
    # List cover files
    cover_result = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=f'{folder}cover')
    covers = [o['Key'] for o in cover_result.get('Contents', [])]
    
    if covers:
        print(f"{folder_name}")
        for c in covers:
            obj = s3.head_object(Bucket='asiandrama-cdn', Key=c)
            size_kb = obj['ContentLength'] / 1024
            print(f"  {c.split('/')[-1]} ({size_kb:.1f} KB)")
    else:
        print(f"{folder_name} - NO COVER FILE!")
    print()
