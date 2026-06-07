"""
COMPLETE AUDIT: Check all dramas for issues
============================================
1. Duplicates in API response
2. Dramas without r2_folder
3. Dramas without cover/thumbnail
4. Dramas with incomplete R2 uploads (no episodes)
5. Generate cleanup SQL
"""
import json
import boto3
from botocore.config import Config
import requests

# R2 Config
s3 = boto3.client(
    's3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

print("=" * 70)
print("COMPLETE DRAMA AUDIT")
print("=" * 70)

# 1. Fetch all dramas from API
print("\n[1/5] Fetching dramas from API...")
response = requests.get("https://tender-connection-production-246f.up.railway.app/api/r2-dramas")
data = response.json()
dramas = data.get('dramas', [])
print(f"    Total dramas in API: {len(dramas)}")

# 2. Find duplicates
print("\n[2/5] Checking for duplicates...")
title_counts = {}
for d in dramas:
    title = d.get('title', 'Unknown')
    if title not in title_counts:
        title_counts[title] = []
    title_counts[title].append(d.get('id'))

duplicates = {t: ids for t, ids in title_counts.items() if len(ids) > 1}
print(f"    Duplicates found: {len(duplicates)}")
for title, ids in duplicates.items():
    print(f"      - '{title}' has {len(ids)} entries: {ids}")

# 3. Check for missing folder_name
print("\n[3/5] Checking for missing folder_name...")
missing_folder = [d for d in dramas if not d.get('folder_name')]
print(f"    Missing folder_name: {len(missing_folder)}")
for d in missing_folder:
    print(f"      - '{d.get('title')}' (ID: {d.get('id')})")

# 4. Check for missing cover
print("\n[4/5] Checking for missing/bad cover URLs...")
missing_cover = [d for d in dramas if not d.get('cover_url') or 'placeholder' in str(d.get('cover_url', '')).lower()]
print(f"    Missing/placeholder cover: {len(missing_cover)}")
for d in missing_cover:
    print(f"      - '{d.get('title')}' (cover: {d.get('cover_url', 'None')[:50]}...)")

# 5. Check R2 for incomplete uploads
print("\n[5/5] Checking R2 for incomplete uploads (no episodes)...")
incomplete_r2 = []
for d in dramas:
    folder_name = d.get('folder_name')
    if not folder_name:
        continue
    
    prefix = f'flickreels/{folder_name}/'
    try:
        r2_response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=50)
        contents = r2_response.get('Contents', [])
        has_episodes = any('ep_' in obj['Key'] and '.m3u8' in obj['Key'] for obj in contents)
        
        if not has_episodes:
            incomplete_r2.append({
                'title': d.get('title'),
                'id': d.get('id'),
                'folder': folder_name,
                'files': [obj['Key'].replace(prefix, '') for obj in contents]
            })
    except Exception as e:
        print(f"      [ERROR] {folder_name}: {e}")

print(f"    Incomplete R2 (no episodes): {len(incomplete_r2)}")
for item in incomplete_r2:
    print(f"      - '{item['title']}' (ID: {item['id']})")
    print(f"        Files: {item['files']}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Total dramas: {len(dramas)}")
print(f"  Duplicates: {len(duplicates)}")
print(f"  Missing folder_name: {len(missing_folder)}")
print(f"  Missing cover: {len(missing_cover)}")
print(f"  Incomplete R2: {len(incomplete_r2)}")

# Generate cleanup SQL
print("\n" + "=" * 70)
print("CLEANUP SQL - Run in Supabase")
print("=" * 70)

sql_lines = []

# Handle duplicates - keep one, delete others
for title, ids in duplicates.items():
    # Keep the first UUID-formatted ID, delete the numeric ones
    uuid_ids = [i for i in ids if '-' in str(i)]
    numeric_ids = [i for i in ids if '-' not in str(i)]
    
    if numeric_ids:
        for nid in numeric_ids:
            sql_lines.append(f"DELETE FROM dramas WHERE flickreels_id = '{nid}';")
    elif len(uuid_ids) > 1:
        # Keep first, delete rest
        for uid in uuid_ids[1:]:
            sql_lines.append(f"DELETE FROM dramas WHERE id = '{uid}';")

# Handle incomplete R2 uploads - unpublish them
for item in incomplete_r2:
    drama_id = item['id']
    if '-' in str(drama_id):
        sql_lines.append(f"UPDATE dramas SET is_published = false WHERE id = '{drama_id}';")
    else:
        sql_lines.append(f"UPDATE dramas SET is_published = false WHERE flickreels_id = '{drama_id}';")

if sql_lines:
    print("\n-- Cleanup SQL:")
    for sql in sql_lines:
        print(sql)
else:
    print("\n-- No cleanup needed!")

# Write to file
with open('cleanup_dramas.sql', 'w', encoding='utf-8') as f:
    f.write("-- Auto-generated cleanup SQL\n")
    f.write("-- Run this in Supabase SQL Editor\n\n")
    for sql in sql_lines:
        f.write(sql + "\n")

print(f"\n[SAVED] cleanup_dramas.sql")
