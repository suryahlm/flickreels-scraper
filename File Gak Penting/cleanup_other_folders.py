#!/usr/bin/env python3
"""Check and delete unused R2 folders"""
import boto3
from botocore.config import Config

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

def list_folder_contents(prefix):
    """List first 20 items in folder"""
    paginator = s3.get_paginator('list_objects_v2')
    items = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, MaxKeys=20):
        for obj in page.get('Contents', []):
            items.append(obj['Key'])
    return items

def delete_folder(prefix):
    """Delete all objects with prefix"""
    deleted = 0
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects = page.get('Contents', [])
        if objects:
            keys = [{'Key': obj['Key']} for obj in objects]
            s3.delete_objects(Bucket=bucket, Delete={'Objects': keys})
            deleted += len(keys)
    return deleted

# Check indonesia/ folder contents
print("=== INDONESIA/ FOLDER CONTENTS ===")
items = list_folder_contents('indonesia/')
for item in items:
    print(f"  {item}")

# Check dramas/ folder contents  
print("\n=== DRAMAS/ FOLDER CONTENTS (first 20) ===")
items = list_folder_contents('dramas/')
for item in items[:20]:
    print(f"  {item}")

# Delete dramas/
print("\n=== DELETING dramas/ ===")
count = delete_folder('dramas/')
print(f"  Deleted {count} objects")

# Delete indonesia/
print("\n=== DELETING indonesia/ ===")
count = delete_folder('indonesia/')
print(f"  Deleted {count} objects")

# Delete data/ and test/
print("\n=== DELETING data/ and test/ ===")
count = delete_folder('data/')
print(f"  Deleted data/: {count} objects")
count = delete_folder('test/')
print(f"  Deleted test/: {count} objects")

print("\n✅ CLEANUP COMPLETE!")
