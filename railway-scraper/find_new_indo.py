#!/usr/bin/env python3
"""Find drama Indonesia baru yang belum ada di Supabase"""
import sys
sys.path.insert(0, '.')
import json
import requests
from local_scraping_indonesia import SUPABASE_CONFIG

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load existing from Supabase
resp = requests.get(
    f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
    headers={"apikey": SUPABASE_CONFIG["key"]}
)
existing = set(str(d['flickreels_id']) for d in resp.json() if d.get('flickreels_id'))

# Load harvest
harvest = json.load(open('harvested_all_dramas.json', 'r', encoding='utf-8'))

# Load Indonesian IDs from sorted file
import re
indo_text = open('sorted_by_language/dramas_indonesian.txt', 'r', encoding='utf-8').read()
indo_ids = [m.group(1) for m in re.finditer(r'^\d+\s+(\d+)\s+', indo_text, re.M)]

# Find new
new_dramas = []
for pid in indo_ids:
    if pid not in existing and pid in harvest:
        d = harvest[pid]
        new_dramas.append((pid, d['title'], d['total_episodes']))

new_dramas.sort(key=lambda x: int(x[0]))

print(f"Total Indonesian terdeteksi: {len(indo_ids)}")
print(f"Sudah di Supabase: {len(indo_ids) - len(new_dramas)}")
print(f"BARU (belum di-scrape): {len(new_dramas)}\n")
print(f"{'No':>3}  {'ID':<6}  {'Judul':<55} {'Episode':>7}")
print("-" * 78)
for i, (pid, title, eps) in enumerate(new_dramas, 1):
    print(f"{i:>3}. [{pid:<5}] {title:<55} {eps:>3} eps")
