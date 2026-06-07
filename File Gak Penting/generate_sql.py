"""
Generate SQL INSERT statements for Supabase (with URL encoding)
================================================================
Reads all drama folders from R2 and generates SQL to import to Supabase.
"""

import json
import urllib.parse
import boto3
from botocore.config import Config

# R2 Configuration
R2_CONFIG = {
    "account_id": "caa84fe6b1be065cda3836f0dac4b509",
    "access_key": "a4903ea93c248388b6e295d6cdbc8617",
    "secret_key": "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9",
    "bucket": "asiandrama-cdn",
}

BASE_URL = "https://tender-connection-production-246f.up.railway.app"

def main():
    print("=" * 60)
    print("GENERATING SQL INSERT SCRIPT (with URL encoding)")
    print("=" * 60)
    
    # Connect to R2
    print("\n[1] Connecting to R2...")
    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_CONFIG['access_key'],
        aws_secret_access_key=R2_CONFIG['secret_key'],
        config=Config(signature_version='s3v4')
    )
    
    # List R2 folders
    print("[2] Listing R2 folders...")
    paginator = s3.get_paginator('list_objects_v2')
    
    folders = []
    for page in paginator.paginate(Bucket=R2_CONFIG['bucket'], Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folder = prefix['Prefix'].replace('flickreels/', '').rstrip('/')
            if folder and folder not in ['test', 'dramas']:
                folders.append(folder)
    
    print(f"    Found {len(folders)} drama folders")
    
    # Generate SQL
    print("\n[3] Generating SQL INSERT statements...")
    sql_lines = []
    sql_lines.append("-- SQL INSERT for R2 Dramas to Supabase")
    sql_lines.append("-- Run this in Supabase Dashboard > SQL Editor")
    sql_lines.append("-- Generated from R2 storage")
    sql_lines.append("")
    sql_lines.append("INSERT INTO dramas (title, synopsis, thumbnail_url, total_episodes, view_count, is_published)")
    sql_lines.append("VALUES")
    
    values = []
    processed = 0
    failed = 0
    
    for folder in folders:
        try:
            # Read metadata
            meta_response = s3.get_object(
                Bucket=R2_CONFIG['bucket'],
                Key=f"flickreels/{folder}/metadata.json"
            )
            metadata = json.loads(meta_response['Body'].read().decode('utf-8'))
            
            # Count episodes
            episode_count = 0
            try:
                ep_response = s3.list_objects_v2(
                    Bucket=R2_CONFIG['bucket'],
                    Prefix=f"flickreels/{folder}/ep_",
                    MaxKeys=200
                )
                for obj in ep_response.get('Contents', []):
                    if obj['Key'].endswith('.m3u8'):
                        episode_count += 1
            except:
                pass
            
            if episode_count == 0:
                episode_count = metadata.get('total_episodes', 0) or metadata.get('chapter_total', 0)
            
            # Get data
            title = metadata.get('title', folder.split('(')[0].strip())
            synopsis = metadata.get('synopsis', '').replace("'", "''")[:500]
            
            # URL encode the folder name for thumbnail
            folder_encoded = urllib.parse.quote(folder, safe='')
            thumbnail_url = f"{BASE_URL}/api/stream/flickreels/{folder_encoded}/cover.jpg"
            
            # Clean title for SQL
            title_clean = title.replace("'", "''")
            
            value_line = f"  ('{title_clean}', '{synopsis}', '{thumbnail_url}', {episode_count}, 0, true)"
            values.append(value_line)
            
            print(f"  [OK] {title[:50]}... ({episode_count} eps)")
            processed += 1
            
        except Exception as e:
            print(f"  [SKIP] {folder[:50]}... (no metadata)")
            failed += 1
    
    # Join values
    sql_lines.append(",\n".join(values))
    sql_lines.append(";")
    
    # Write to file
    sql_content = "\n".join(sql_lines)
    output_file = "import_dramas.sql"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sql_content)
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"  Processed: {processed}")
    print(f"  Skipped: {failed}")
    print(f"  SQL file: {output_file}")
    print("=" * 60)
    print("\nNext step: Open import_dramas.sql and copy to Supabase SQL Editor!")

if __name__ == "__main__":
    main()
