#!/usr/bin/env python3
"""Check R2 folder and metadata statistics."""

import boto3
from botocore.config import Config
import os

def main():
    # Load .env
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip('"').strip("'")

    s3 = boto3.client('s3',
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4')
    )

    bucket = os.environ['R2_BUCKET_NAME']
    
    # List all folders
    resp = s3.list_objects_v2(Bucket=bucket, Prefix='flickreels/', Delimiter='/')
    folders = [p['Prefix'] for p in resp.get('CommonPrefixes', [])]
    
    # Handle pagination
    while resp.get('IsTruncated'):
        resp = s3.list_objects_v2(
            Bucket=bucket, 
            Prefix='flickreels/', 
            Delimiter='/',
            ContinuationToken=resp['NextContinuationToken']
        )
        folders.extend([p['Prefix'] for p in resp.get('CommonPrefixes', [])])
    
    print(f"Total folders in R2: {len(folders)}")
    
    # Count those with metadata.json
    with_meta = 0
    without_meta = []
    
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        try:
            s3.head_object(Bucket=bucket, Key=f'{folder}metadata.json')
            with_meta += 1
        except:
            without_meta.append(folder_name)
    
    print(f"Folders with metadata.json: {with_meta}")
    print(f"Folders WITHOUT metadata.json: {len(without_meta)}")
    
    if without_meta and len(without_meta) <= 20:
        print("\nMissing metadata folders:")
        for f in without_meta:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
