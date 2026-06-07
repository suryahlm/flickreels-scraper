"""Check R2 episode counts for ALL dramas and compare with database"""
import json
import boto3
import requests
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

# Get dramas from API
response = requests.get("https://tender-connection-production-246f.up.railway.app/api/r2-dramas")
dramas = response.json().get('dramas', [])

mismatches = []
ok_count = 0

for d in dramas:
    folder_name = d.get('folder_name')
    db_episodes = d.get('total_episodes', 0)
    
    if not folder_name:
        continue
    
    # Count R2 episodes
    prefix = f'flickreels/{folder_name}/'
    r2_response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=200)
    contents = r2_response.get('Contents', [])
    r2_episodes = len([c for c in contents if 'ep_' in c['Key'] and '.m3u8' in c['Key']])
    
    if r2_episodes != db_episodes:
        mismatches.append({
            'id': d.get('id'),
            'folder': folder_name,
            'r2': r2_episodes,
            'db': db_episodes
        })
    else:
        ok_count += 1

print(f"OK: {ok_count}")
print(f"MISMATCH: {len(mismatches)}")
print()

if mismatches:
    print("MISMATCHES:")
    for m in mismatches:
        print(f"  R2={m['r2']}, DB={m['db']} | {m['folder'][:50]}")
    
    print()
    print("SQL TO FIX:")
    for m in mismatches:
        print(f"UPDATE dramas SET total_episodes = {m['r2']} WHERE id = '{m['id']}';")
