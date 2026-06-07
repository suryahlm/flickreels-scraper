"""Deep check: Compare R2 episodes with database for ALL dramas"""
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

print("=" * 80)
print("DEEP R2 AUDIT - Checking ALL dramas for episode count mismatches")
print("=" * 80)

# Get dramas from API
response = requests.get("https://tender-connection-production-246f.up.railway.app/api/r2-dramas")
dramas = response.json().get('dramas', [])

print(f"\nGot {len(dramas)} dramas from database\n")

mismatches = []
critical_issues = []

for d in dramas:
    folder_name = d.get('folder_name')
    db_episodes = d.get('total_episodes', 0)
    title = d.get('title', 'Unknown')
    drama_id = d.get('id')
    
    if not folder_name:
        critical_issues.append(f"NO FOLDER: {title} (ID: {drama_id})")
        continue
    
    # Count actual episodes in R2
    prefix = f'flickreels/{folder_name}/'
    try:
        r2_response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=500)
        contents = r2_response.get('Contents', [])
        r2_episodes = len([c for c in contents if 'ep_' in c['Key'] and c['Key'].endswith('.m3u8')])
        
        # Check for mismatch
        if r2_episodes != db_episodes:
            diff = r2_episodes - db_episodes
            status = "MORE" if diff > 0 else "LESS"
            mismatches.append({
                'title': title,
                'id': drama_id,
                'folder': folder_name,
                'r2': r2_episodes,
                'db': db_episodes,
                'diff': diff,
                'status': status
            })
            
            # Critical: R2 has MORE episodes than DB (DB is outdated)
            if diff > 0:
                print(f"⚠️  {title[:45]:45s} | DB={db_episodes:3d} R2={r2_episodes:3d} (+{diff})")
            else:
                print(f"❌ {title[:45]:45s} | DB={db_episodes:3d} R2={r2_episodes:3d} ({diff})")
        else:
            print(f"✅ {title[:45]:45s} | {r2_episodes:3d} episodes")
            
    except Exception as e:
        critical_issues.append(f"R2 ERROR: {title} - {str(e)[:50]}")

print("\n" + "=" * 80)
print(f"SUMMARY: {len(mismatches)} mismatches found")
print("=" * 80)

if critical_issues:
    print("\n⚠️  CRITICAL ISSUES:")
    for issue in critical_issues:
        print(f"  {issue}")

if mismatches:
    print("\n📊 DETAILED MISMATCHES:")
    
    # Separate into categories
    more_in_r2 = [m for m in mismatches if m['diff'] > 0]
    less_in_r2 = [m for m in mismatches if m['diff'] < 0]
    
    if more_in_r2:
        print(f"\n✅ R2 HAS MORE (DB needs update): {len(more_in_r2)} dramas")
        for m in more_in_r2[:10]:
            print(f"  {m['title'][:40]:40s} | DB={m['db']:3d} → R2={m['r2']:3d} (+{m['diff']})")
    
    if less_in_r2:
        print(f"\n❌ R2 HAS LESS (Episodes missing!): {len(less_in_r2)} dramas")
        for m in less_in_r2:
            print(f"  {m['title'][:40]:40s} | DB={m['db']:3d} → R2={m['r2']:3d} ({m['diff']})")
    
    # Generate SQL fix
    print("\n" + "=" * 80)
    print("SQL TO FIX DATABASE (update to match R2):")
    print("=" * 80)
    
    with open('fix_episode_counts_full.sql', 'w', encoding='utf-8') as f:
        f.write("-- Fix episode counts to match R2 actual count\n\n")
        for m in mismatches:
            sql = f"UPDATE dramas SET total_episodes = {m['r2']} WHERE id = '{m['id']}';"
            f.write(sql + "\n")
            print(sql)
    
    print(f"\n💾 Saved to: fix_episode_counts_full.sql")

# Special check for "Tak Bisa Melepasmu"
print("\n" + "=" * 80)
print("SPECIAL CHECK: Tak Bisa Melepasmu")
print("=" * 80)

tak_bisa = [d for d in dramas if 'Tak Bisa Melepasmu' in d.get('title', '')]
if tak_bisa:
    d = tak_bisa[0]
    folder = d.get('folder_name')
    print(f"Title: {d.get('title')}")
    print(f"ID: {d.get('id')}")
    print(f"Folder: {folder}")
    print(f"DB Episodes: {d.get('total_episodes')}")
    
    if folder:
        prefix = f'flickreels/{folder}/'
        r2_response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=prefix, MaxKeys=500)
        contents = r2_response.get('Contents', [])
        episodes = [c['Key'] for c in contents if 'ep_' in c['Key'] and c['Key'].endswith('.m3u8')]
        print(f"R2 Episodes: {len(episodes)}")
        
        if len(episodes) > 0:
            print(f"\nFirst 5 episodes:")
            for ep in sorted(episodes)[:5]:
                print(f"  {ep}")
            print(f"Last 5 episodes:")
            for ep in sorted(episodes)[-5:]:
                print(f"  {ep}")
