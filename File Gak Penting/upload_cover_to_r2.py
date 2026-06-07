"""
Upload single cover image to R2
"""
import os
import sys
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# R2 Config
R2_CONFIG = {
    "account_id": os.environ.get("R2_ACCOUNT_ID", ""),
    "access_key_id": os.environ.get("R2_ACCESS_KEY_ID", ""),
    "secret_access_key": os.environ.get("R2_SECRET_ACCESS_KEY", ""),
    "bucket_name": os.environ.get("R2_BUCKET_NAME", "asiandrama-cdn"),
}

# Setup S3 client
s3 = boto3.client(
    's3',
    endpoint_url=f'https://{R2_CONFIG["account_id"]}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_CONFIG["access_key_id"],
    aws_secret_access_key=R2_CONFIG["secret_access_key"],
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

# Upload cover
drama_id = "3108"
drama_title = "Ayah Pacarku, Suamiku"
folder_name = f"{drama_title} ({drama_id})"
local_path = Path(f"Video Drama TS/30.01.2026/{folder_name}/cover.jpg")

if not local_path.exists():
    print(f"❌ Cover not found: {local_path}")
    sys.exit(1)

r2_key = f"flickreels/{folder_name}/cover.jpg"

print(f"Uploading: {local_path}")
print(f"To R2: {r2_key}")

try:
    s3.upload_file(
        str(local_path),
        R2_CONFIG["bucket_name"],
        r2_key,
        ExtraArgs={'ContentType': 'image/jpeg'}
    )
    print(f"✅ Uploaded successfully!")
    print(f"URL: https://pub-caa84fe6b1be065c.r2.dev/{r2_key}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
