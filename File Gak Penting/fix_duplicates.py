"""
Fix duplicates in Supabase - keep only entries with correct Railway stream URL
"""
import requests

SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

# Get all dramas
resp = requests.get(f'{SUPABASE_URL}/rest/v1/dramas?select=id,flickreels_id,thumbnail_url', headers=headers)
dramas = resp.json()
print(f'Total entries: {len(dramas)}')

# Group by flickreels_id, keep only entries with Railway stream URL
by_fid = {}
for d in dramas:
    fid = d['flickreels_id']
    thumb = d.get('thumbnail_url', '') or ''
    has_railway = 'tender-connection' in thumb
    
    if fid not in by_fid:
        by_fid[fid] = {'keep': None, 'delete': []}
    
    if has_railway and by_fid[fid]['keep'] is None:
        by_fid[fid]['keep'] = d
    else:
        by_fid[fid]['delete'].append(d)

# Delete all extras
delete_count = 0
for fid, data in by_fid.items():
    for d in data['delete']:
        resp = requests.delete(
            f"{SUPABASE_URL}/rest/v1/dramas?id=eq.{d['id']}",
            headers=headers
        )
        print(f"Deleted {d['id']} (fid={fid}): {resp.status_code}")
        delete_count += 1

print(f'\nDeleted {delete_count} duplicates')

# Final count
resp = requests.get(f'{SUPABASE_URL}/rest/v1/dramas?select=id,flickreels_id,title,thumbnail_url', headers=headers)
final = resp.json()
print(f'Final count: {len(final)}')
for d in final:
    thumb = d.get('thumbnail_url', '')[:50] if d.get('thumbnail_url') else 'NONE'
    print(f"  {d['flickreels_id']}: {d['title'][:30]} -> {thumb}...")
