#!/usr/bin/env python3
"""Delete 5 English dramas from R2 and Supabase"""
import boto3
from botocore.config import Config
import requests

# R2 Config
r2 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

# Supabase Config
SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

# Dramas to delete
dramas = [
    ('55', "Country Girl, CEO's Wife"),
    ('54', 'Oh No! My Boss Is My Secret Lover'),
    ('36', 'Online Boyfriend is My Boss'),
    ('35', "Intern is CEO's Wife"),
    ('17', 'Body Swap: CEO And the Princess')
]

bucket = 'asiandrama-cdn'

for fid, title in dramas:
    print(f'\nDeleting {title} (ID: {fid})...')
    
    # Get r2_folder from Supabase
    resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{fid}&select=r2_folder',
        headers={'apikey': SUPABASE_KEY}
    )
    data = resp.json()
    if not data:
        print(f'  Not found in Supabase')
        continue
    
    r2_folder = data[0].get('r2_folder', '')
    if r2_folder:
        prefix = f'flickreels/{r2_folder}/'
        print(f'  R2 prefix: {prefix}')
        
        # List and delete objects
        paginator = r2.get_paginator('list_objects_v2')
        deleted = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            objects = page.get('Contents', [])
            if objects:
                r2.delete_objects(
                    Bucket=bucket,
                    Delete={'Objects': [{'Key': obj['Key']} for obj in objects]}
                )
                deleted += len(objects)
        print(f'  R2: Deleted {deleted} objects')
    
    # Delete from Supabase
    del_resp = requests.delete(
        f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{fid}',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
    )
    print(f'  Supabase: Deleted (status {del_resp.status_code})')

print('\n✅ Done!')
