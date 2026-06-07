#!/usr/bin/env python3
"""Check episode file structure for different dramas."""
import boto3
from botocore.config import Config

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# Check a drama WITH cover (old format - complete)
old_drama = 'flickreels/Tak Bisa Melepasmu (2858)/'
print(f"=== OLD FORMAT (with cover): {old_drama} ===")
try:
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=old_drama, MaxKeys=20)
    for obj in resp.get('Contents', [])[:20]:
        print(f"  {obj['Key'].replace(old_drama, '')}")
except Exception as e:
    print(f"  Error: {e}")

# Check a drama WITHOUT cover (new format - episodes subdir)
new_drama = 'flickreels/Chasse au tueur  Maman, sauvez-moi ! (3491)/'
print(f"\n=== NEW FORMAT (no cover): {new_drama} ===")
try:
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=new_drama, MaxKeys=30)
    for obj in resp.get('Contents', [])[:30]:
        print(f"  {obj['Key'].replace(new_drama, '')}")
except Exception as e:
    print(f"  Error: {e}")

# Check another new drama
another = 'flickreels/A Kiss on the Thorny Rose (3891)/'
print(f"\n=== ANOTHER NEW FORMAT: {another} ===")
try:
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=another, MaxKeys=20)
    for obj in resp.get('Contents', [])[:20]:
        print(f"  {obj['Key'].replace(another, '')}")
except Exception as e:
    print(f"  Error: {e}")
