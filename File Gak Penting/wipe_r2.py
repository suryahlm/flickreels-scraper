"""
Wipe all content from R2 bucket
"""
import boto3

# R2 credentials
R2_ACCOUNT_ID = "caa84fe6b1be065cda3836f0dac4b509"
R2_ACCESS_KEY_ID = "a4903ea93c248388b6e295d6cdbc8617"
R2_SECRET_ACCESS_KEY = "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"
R2_BUCKET_NAME = "asiandrama-cdn"

# Create S3 client for R2
s3 = boto3.client('s3',
    endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY
)

print("🗑️ Wiping all content from R2 bucket...")
print(f"Bucket: {R2_BUCKET_NAME}")
print()

deleted_count = 0
paginator = s3.get_paginator('list_objects_v2')

for page in paginator.paginate(Bucket=R2_BUCKET_NAME):
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
            print(f"Deleting: {key}")
            s3.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
            deleted_count += 1

print()
print(f"✅ Done! Deleted {deleted_count} objects.")
