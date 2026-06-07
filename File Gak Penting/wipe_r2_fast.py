"""
FAST Wipe - Delete 1000 objects per API call
"""
import boto3

R2_ACCOUNT_ID = "caa84fe6b1be065cda3836f0dac4b509"
R2_ACCESS_KEY_ID = "a4903ea93c248388b6e295d6cdbc8617"
R2_SECRET_ACCESS_KEY = "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"
R2_BUCKET_NAME = "asiandrama-cdn"

s3 = boto3.client('s3',
    endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY
)

print("🗑️ FAST WIPE - 1000 objects per batch")
print(f"Bucket: {R2_BUCKET_NAME}\n")

deleted = 0
paginator = s3.get_paginator('list_objects_v2')

for page in paginator.paginate(Bucket=R2_BUCKET_NAME):
    if 'Contents' not in page:
        continue
    
    # Batch delete up to 1000 objects at once
    objects = [{'Key': obj['Key']} for obj in page['Contents']]
    
    if objects:
        s3.delete_objects(Bucket=R2_BUCKET_NAME, Delete={'Objects': objects, 'Quiet': True})
        deleted += len(objects)
        print(f"Deleted batch: {len(objects)} objects (total: {deleted})")

print(f"\n✅ Done! Deleted {deleted} objects.")
