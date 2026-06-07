#!/usr/bin/env python3
"""
Proper comparison with Supabase - using correct URL
"""
import json
import requests
import time

# CORRECT Supabase URL and KEY
SUPABASE_URL = "https://bmryonqbddbkjbtquhgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"

print("Fetching all dramas from Supabase...")

# Get all dramas
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/dramas?select=id,flickreels_id,title",
    headers={"apikey": SUPABASE_KEY},
    timeout=60
)

if resp.status_code != 200:
    print(f"Error: {resp.status_code} - {resp.text}")
    exit(1)

existing = resp.json()
print(f"Got {len(existing)} dramas from Supabase")

# Build lookup sets
existing_ids = set()
existing_titles = set()
for d in existing:
    if d.get('flickreels_id'):
        existing_ids.add(str(d['flickreels_id']))
    if d.get('title'):
        existing_titles.add(d['title'].lower().strip())

print(f"Existing IDs: {len(existing_ids)}")
print(f"Existing unique titles: {len(existing_titles)}")

# Load discovered
with open("comprehensive_dramas.json", "r", encoding="utf-8") as f:
    discovered = json.load(f)

print(f"\nDiscovered: {len(discovered)} dramas from API")

# Compare
truly_new = []
already_have_by_id = []
already_have_by_title = []

for d in discovered:
    drama_id = str(d['id'])
    title = d.get('title', '').lower().strip()
    
    if drama_id in existing_ids:
        already_have_by_id.append(d)
    elif title in existing_titles:
        already_have_by_title.append(d)
    else:
        truly_new.append(d)

print(f"\n" + "="*60)
print("HASIL PERBANDINGAN:")
print("="*60)
print(f"  Sudah ada (by ID): {len(already_have_by_id)}")
print(f"  Sudah ada (by title, beda ID): {len(already_have_by_title)}")
print(f"  BENAR-BENAR BARU: {len(truly_new)}")

# Show some that match by title but not ID
if already_have_by_title:
    print(f"\nDrama dengan judul sama tapi ID berbeda:")
    for d in already_have_by_title[:15]:
        print(f"  ID {d['id']}: {d.get('title', 'N/A')[:50]}")

# Export truly new
truly_new_sorted = sorted(truly_new, key=lambda x: int(x['id']) if str(x['id']).isdigit() else 0)

with open("new_dramas_list.txt", "w", encoding="utf-8") as f:
    f.write("DRAMA BARU YANG BENAR-BENAR BELUM ADA\n")
    f.write(f"Total: {len(truly_new_sorted)} drama\n")
    f.write("=" * 60 + "\n\n")
    
    for i, d in enumerate(truly_new_sorted, 1):
        f.write(f"{i:3}. [{d['id']:>5}] {d.get('title', 'N/A')}\n")

print(f"\nSaved to new_dramas_list.txt")
