"""Check if nested folders were created in R2"""
import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'
prefix = 'flickreels/'

print("Checking R2 for nested folder structure...\n")

# List all items
response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=100)
contents = response.get('Contents', [])

print(f"Found {len(contents)} recent files:\n")

# Group by drama and episode
dramas = {}
for obj in contents:
    key = obj['Key']
    parts = key.split('/')
    
    if len(parts) >= 3:
        drama = parts[1]  # Drama folder
        if len(parts) == 4 and parts[2].startswith('ep_'):
            # Episode folder detected!
            episode = parts[2]
            filename = parts[3]
            
            if drama not in dramas:
                dramas[drama] = {}
            if episode not in dramas[drama]:
                dramas[drama][episode] = []
            dramas[drama][episode].append(filename)

if dramas:
    print("✅ NESTED STRUCTURE DETECTED!\n")
    for drama, episodes in dramas.items():
        print(f"📁 {drama}/")
        for ep, files in sorted(episodes.items()):
            print(f"  └─ {ep}/ ({len(files)} files)")
            for f in files[:3]:
                print(f"      - {f}")
            if len(files) > 3:
                print(f"      ... and {len(files)-3} more")
else:
    print("❌ No nested structure found")
    print("\nShowing recent files:")
    for obj in contents[:20]:
        print(f"  {obj['Key']}")
