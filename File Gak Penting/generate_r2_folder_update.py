"""
Generate SQL UPDATE statements to set r2_folder for each drama
================================================================
Matches drama titles in Supabase to R2 folder names.
"""

import json
import boto3
from botocore.config import Config

# R2 Configuration
R2_CONFIG = {
    "account_id": "caa84fe6b1be065cda3836f0dac4b509",
    "access_key": "a4903ea93c248388b6e295d6cdbc8617",
    "secret_key": "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9",
    "bucket": "asiandrama-cdn",
}

def main():
    print("=" * 60)
    print("GENERATING SQL UPDATE FOR r2_folder")
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
    print("\n[3] Generating SQL UPDATE statements...")
    sql_lines = []
    sql_lines.append("-- SQL UPDATE to set r2_folder for each drama")
    sql_lines.append("-- Run this AFTER running add_r2_folder_column.sql")
    sql_lines.append("")
    
    processed = 0
    
    for folder in folders:
        try:
            # Read metadata
            meta_response = s3.get_object(
                Bucket=R2_CONFIG['bucket'],
                Key=f"flickreels/{folder}/metadata.json"
            )
            metadata = json.loads(meta_response['Body'].read().decode('utf-8'))
            
            # Get title
            title = metadata.get('title', folder.split('(')[0].strip())
            title_escaped = title.replace("'", "''")
            folder_escaped = folder.replace("'", "''")
            
            sql_lines.append(f"UPDATE dramas SET r2_folder = '{folder_escaped}' WHERE title = '{title_escaped}';")
            
            print(f"  [OK] {title[:40]}... -> {folder[:30]}...")
            processed += 1
            
        except Exception as e:
            print(f"  [SKIP] {folder[:40]}... (no metadata)")
    
    # Write to file
    sql_content = "\n".join(sql_lines)
    output_file = "update_r2_folders.sql"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(sql_content)
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"  Processed: {processed}")
    print(f"  SQL file: {output_file}")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run add_r2_folder_column.sql in Supabase")
    print("2. Run update_r2_folders.sql in Supabase")

if __name__ == "__main__":
    main()
