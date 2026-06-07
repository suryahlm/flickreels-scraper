#!/usr/bin/env python3
"""Check what's in R2 for failed episode: Jangan Ganggu Nenek ep_001"""
import boto3, os

with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v.strip('"').strip("'")

r2 = boto3.client('s3',
    endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'])

bucket = os.environ['R2_BUCKET_NAME']
prefix = 'flickreels/Jangan Ganggu Nenek (5235)/'

# List all objects
resp = r2.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=100)
objects = resp.get('Contents', [])

# Also check subfolders
resp2 = r2.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
subs = [p['Prefix'] for p in resp2.get('CommonPrefixes', [])]

print(f"Prefix: {prefix}")
print(f"Subfolders: {len(subs)}")
for s in subs[:10]:
    print(f"  {s}")
print(f"\nDirect objects: {len(objects)}")
for o in objects[:20]:
    print(f"  {o['Key']}  ({o['Size']} bytes)")

# Check if ep_001.mp4 exists
try:
    head = r2.head_object(Bucket=bucket, Key=f"{prefix}ep_001.mp4")
    print(f"\nep_001.mp4 EXISTS ({head['ContentLength']} bytes)")
except:
    print(f"\nep_001.mp4 DOES NOT EXIST")

# Check ep_001/ folder
try:
    resp3 = r2.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}ep_001/", MaxKeys=5)
    hls = resp3.get('Contents', [])
    print(f"ep_001/ HLS files: {len(hls)}")
    for o in hls:
        print(f"  {o['Key']}")
except:
    print("ep_001/ folder not found")
