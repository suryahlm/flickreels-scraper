"""
Delete Nenek Muda dramas with correct folder names
"""
import boto3
import os
from pathlib import Path

# R2 Configuration
R2_ACCOUNT_ID = 'b1862cef73b53f55f8e66fa29c3b1e3d'
R2_ACCESS_KEY_ID = '7e4d66e23ce0e9ad61a41cb9c9be38e0'
R2_SECRET_ACCESS_KEY = '6dc6fc06dfd2e3976f21c3df00e37dc95eb7f79f5e7e8e26e614c5f0d89f0a80'
R2_BUCKET_NAME = 'asiandrama-cdn'

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())
    
    R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID', R2_ACCOUNT_ID)
    R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', R2_ACCESS_KEY_ID)
    R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', R2_SECRET_ACCESS_KEY)
    R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', R2_BUCKET_NAME)

# Create S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name='auto'
)

# Nenek Muda dramas to delete (with underscore)
dramas_to_delete = [
    "Nenek Muda_ Kebangkitan Keluarga (1525)",
    "Nenek Muda_ Kebangkitan Keluarga(Dubbing) (1976)",
]

print("="*60)
print("DELETING NENEK MUDA DRAMAS FROM R2")
print("="*60)

for folder_name in dramas_to_delete:
    print(f"\nDeleting: {folder_name}")
    
    prefix = f"flickreels/{folder_name}/"
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=R2_BUCKET_NAME, Prefix=prefix)
        
        deleted_count = 0
        for page in pages:
            if 'Contents' not in page:
                print(f"  ⚠️  Folder not found in R2")
                break
                
            objects = [{'Key': obj['Key']} for obj in page['Contents']]
            
            if objects:
                s3_client.delete_objects(
                    Bucket=R2_BUCKET_NAME,
                    Delete={'Objects': objects}
                )
                deleted_count += len(objects)
        
        if deleted_count > 0:
            print(f"  ✅ Deleted {deleted_count} files from R2")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print(f"\n{'='*60}")
print("DONE! Total 6 dramas deleted from R2")
print(f"{'='*60}\n")
