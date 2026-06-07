"""
Find all incomplete dramas in R2 (have metadata but no episodes)
"""
import json
import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

print("=" * 60)
print("FINDING INCOMPLETE DRAMAS")
print("=" * 60)

# List all folders
paginator = s3.get_paginator('list_objects_v2')
folders = []
for page in paginator.paginate(Bucket='asiandrama-cdn', Prefix='flickreels/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        folder = prefix['Prefix'].replace('flickreels/', '').rstrip('/')
        if folder and folder not in ['test', 'dramas']:
            folders.append(folder)

print(f"Total folders: {len(folders)}")

complete = []
incomplete = []

for folder in folders:
    prefix = f'flickreels/{folder}/'
    response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=100)
    contents = response.get('Contents', [])
    
    # Check for episode files
    has_episodes = any('ep_' in obj['Key'] and '.m3u8' in obj['Key'] for obj in contents)
    
    if has_episodes:
        complete.append(folder)
    else:
        incomplete.append(folder)
        print(f"  [INCOMPLETE] {folder[:50]}...")

print()
print("=" * 60)
print(f"COMPLETE: {len(complete)}")
print(f"INCOMPLETE: {len(incomplete)}")
print("=" * 60)

if incomplete:
    print("\nINCOMPLETE DRAMAS (need to be removed from Supabase):")
    for folder in incomplete:
        print(f"  - {folder}")
    
    # Generate SQL to set is_published = false for incomplete dramas
    print("\n\nSQL to unpublish incomplete dramas:")
    print("-" * 40)
    for folder in incomplete:
        # Get title from folder
        title = folder.split(' (')[0]
        title_escaped = title.replace("'", "''")
        print(f"UPDATE dramas SET is_published = false WHERE title LIKE '{title_escaped}%';")
