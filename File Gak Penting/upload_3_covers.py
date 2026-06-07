"""
Upload 3 specific covers to R2
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

dramas = [
    "Sayang, Aku Benaran Amnesia (3164)",
    "Kejayaanku Setelah Berpisah (963)",
    "Istri Kesayangan Mafia (495)",
]

base_path = Path("Video Drama TS/30.01.2026")

print("="*60)
print("UPLOADING MISSING COVERS TO R2")
print("="*60)

for folder_name in dramas:
    print(f"\n📤 Processing: {folder_name}")
    
    local_cover = base_path / folder_name / "cover.jpg"
    
    if not local_cover.exists():
        print(f"  ❌ Local cover not found: {local_cover}")
        continue
    
    # Check if already in R2
    r2_key = f"flickreels/{folder_name}/cover.jpg"
    
    try:
        s3_client.head_object(Bucket=R2_BUCKET_NAME, Key=r2_key)
        print(f"  ✅ Already exists in R2: {r2_key}")
        continue
    except:
        pass  # Not in R2, need to upload
    
    # Upload to R2
    try:
        with open(local_cover, 'rb') as f:
            s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=r2_key,
                Body=f,
                ContentType='image/jpeg'
            )
        
        size = local_cover.stat().st_size
        print(f"  ✅ Uploaded to R2: {r2_key} ({size:,} bytes)")
        
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")

print(f"\n{'='*60}")
print("UPLOAD COMPLETE")
print(f"{'='*60}\n")
