"""Check episode count for ALL dramas in R2"""
import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

print("=" * 70)
print("R2 EPISODE COUNT FOR ALL DRAMAS")
print("=" * 70)

# List all folders in flickreels/
paginator = s3.get_paginator('list_objects_v2')
folders = set()

for page in paginator.paginate(Bucket='asiandrama-cdn', Prefix='flickreels/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        folder = prefix['Prefix'].replace('flickreels/', '').rstrip('/')
        folders.add(folder)

print(f"Found {len(folders)} drama folders in R2\n")

total_episodes = 0
drama_list = []

for folder in sorted(folders):
    # Count m3u8 files in each folder
    prefix = f'flickreels/{folder}/'
    response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=500)
    contents = response.get('Contents', [])
    
    # Count episode files (ep_XXX.m3u8)
    ep_count = len([c for c in contents if 'ep_' in c['Key'] and c['Key'].endswith('.m3u8')])
    
    total_episodes += ep_count
    drama_list.append((folder, ep_count))
    
    # Truncate folder name for display
    display_name = folder[:50] + '...' if len(folder) > 50 else folder
    print(f"{ep_count:3d} eps | {display_name}")

print()
print("=" * 70)
print(f"TOTAL: {len(folders)} dramas, {total_episodes} episodes in R2")
print("=" * 70)

# Show top 10 dramas by episode count
print("\nTOP 10 BY EPISODE COUNT:")
for folder, count in sorted(drama_list, key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {count:3d} eps | {folder[:50]}")
