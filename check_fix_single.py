#!/usr/bin/env python3
"""Check and fix failed episode: Takluk dalam Hasrat (4221) ep_043"""
import os
from dotenv import load_dotenv
import boto3

load_dotenv()

r2 = boto3.client('s3',
    endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
    region_name='auto'
)
BUCKET = os.environ.get('R2_BUCKET_NAME', 'asiandrama-cdn')

prefix = "flickreels/Takluk dalam Hasrat (4221)/ep_043/"
print(f"Checking: {prefix}")

resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=prefix, MaxKeys=30)
contents = resp.get('Contents', [])

if not contents:
    print("  EMPTY - no HLS files exist. Source was never uploaded or already cleaned.")
    print("  This episode cannot be fixed - source data missing from provider.")
else:
    print(f"  Found {len(contents)} files:")
    for obj in contents:
        fname = obj['Key'].split('/')[-1]
        size_mb = obj['Size'] / 1024 / 1024
        print(f"    {fname} ({size_mb:.2f} MB)")
    
    # Check if m3u8 exists
    has_m3u8 = any(c['Key'].endswith('.m3u8') for c in contents)
    if not has_m3u8:
        print("\n  ⚠️  Missing index.m3u8 - cannot convert without manifest")
        print("  Cleaning up orphaned segments...")
        for obj in contents:
            r2.delete_object(Bucket=BUCKET, Key=obj['Key'])
        print(f"  🗑️  Deleted {len(contents)} orphaned files")
    else:
        print("\n  ✅ Has m3u8 - attempting fix...")
