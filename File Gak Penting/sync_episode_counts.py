"""Generate SQL to update total_episodes in Supabase based on actual R2 episode count"""
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

print("Fetching dramas from API...")

# Get dramas from API (which comes from Supabase)
response = requests.get("https://tender-connection-production-246f.up.railway.app/api/r2-dramas")
dramas = response.json().get('dramas', [])

print(f"Got {len(dramas)} dramas from API")
print()

# Build folder name to drama map
drama_map = {}
for d in dramas:
    folder = d.get('folder_name')
    if folder:
        drama_map[folder] = {
            'id': d.get('id'),
            'title': d.get('title'),
            'db_episodes': d.get('total_episodes', 0)
        }

# Count actual R2 episodes for each drama
sql_updates = []
mismatches = []

for folder, info in drama_map.items():
    prefix = f'flickreels/{folder}/'
    r2_response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=500)
    contents = r2_response.get('Contents', [])
    r2_episodes = len([c for c in contents if 'ep_' in c['Key'] and c['Key'].endswith('.m3u8')])
    
    if r2_episodes != info['db_episodes']:
        mismatches.append({
            'folder': folder,
            'id': info['id'],
            'title': info['title'],
            'db': info['db_episodes'],
            'r2': r2_episodes
        })
        sql_updates.append(f"UPDATE dramas SET total_episodes = {r2_episodes} WHERE id = '{info['id']}';")

print("=" * 70)
print(f"MISMATCHES: {len(mismatches)} dramas need update")
print("=" * 70)

for m in mismatches:
    print(f"  DB={m['db']:3d} -> R2={m['r2']:3d} | {m['title'][:40]}")

print()
print("=" * 70)
print("SQL TO UPDATE (copy to Supabase):")
print("=" * 70)

# Write SQL to file
with open('update_episode_counts.sql', 'w', encoding='utf-8') as f:
    f.write("-- Update total_episodes to match R2 episode count\n")
    f.write("-- Generated automatically\n\n")
    for sql in sql_updates:
        f.write(sql + "\n")
        print(sql)

print()
print(f"Saved to: update_episode_counts.sql")
