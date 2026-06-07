"""Test script to verify progress loading from Supabase"""
import requests

SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

# Test: Load existing IDs from Supabase
resp = requests.get(f'{SUPABASE_URL}/rest/v1/dramas?select=flickreels_id', headers={'apikey': SUPABASE_KEY})
scraped_ids = set()
for d in resp.json():
    if d.get('flickreels_id'):
        scraped_ids.add(str(d['flickreels_id']))

print(f'Loaded {len(scraped_ids)} already scraped IDs:')
for sid in scraped_ids:
    print(f'  - {sid}')

# Test filter logic
test_dramas = [
    {'id': 5247, 'title': 'Peramal Wanita'},  # Already exists
    {'id': 1675, 'title': 'CEO itu Ayah Anakku'},  # Already exists
    {'id': 9999, 'title': 'New Drama'},  # New
]

to_scrape = [d for d in test_dramas if str(d['id']) not in scraped_ids]
print(f'\nWill scrape {len(to_scrape)} new dramas:')
for d in to_scrape:
    print(f"  - {d['title']}")
