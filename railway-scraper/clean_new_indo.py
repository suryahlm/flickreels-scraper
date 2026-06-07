#!/usr/bin/env python3
"""Bersihkan daftar drama Indonesia baru — buang false positive & tandai duplikat"""
import sys
sys.path.insert(0, '.')
import re
import json
import requests
from collections import defaultdict
from local_scraping_indonesia import SUPABASE_CONFIG

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# --- FALSE POSITIVE IDs (Spanish/French/Portuguese yang salah masuk) ---
FALSE_POSITIVE_IDS = {
    "731",   # Si el amor tuviera magia (Spanish)
    "1229",  # Rosa Para Mí (Spanish)
    "1839",  # El Favoritismo de Papá Casi Me Mata (Spanish)
    "1957",  # Una receta para el amor (Spanish)
    "2105",  # Si el Amor es Destino (Spanish)
    "2388",  # Pas si divine, la pêche ! (French)
    "2424",  # Para hacerte mía, cuñada (Spanish)
    "2511",  # 99 Días para Enamorarte (Spanish)
    "2701",  # Renací para arruinar a mi amiga (Spanish)
    "2775",  # 30 Días Para Decir Adiós (Spanish)
    "3114",  # Jasmin, si délicat (French)
    "3338",  # Vem para Meu Abraço (Portuguese)
    "3533",  # Renacida para amar al marqués (Spanish)
    "3754",  # Para hacerte mía, cuñada (Doblado) (Spanish)
    "3824",  # Estrategia para Ascender (Spanish)
    "4451",  # Como Era Para Ser (Portuguese)
    "4479",  # Llamada final para el amor (Spanish)
    "4580",  # Voltar para antigo a receber mulher (Portuguese)
    "4853",  # Renací en los 80 para mi amor (Spanish)
    "4940",  # Sin cura para la conciencia (Spanish)
    "4965",  # Um casamento para Sempre (Portuguese)
    "5055",  # Seis vidas para amarte (Spanish)
    "5208",  # Para onde você está (Portuguese)
}

# Load existing from Supabase (with titles for duplicate check)
resp = requests.get(
    f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id,title",
    headers={"apikey": SUPABASE_CONFIG["key"]}
)
existing_ids = set()
existing_titles = set()
for d in resp.json():
    if d.get('flickreels_id'):
        existing_ids.add(str(d['flickreels_id']))
    if d.get('title'):
        existing_titles.add(d['title'].strip().lower())

# Load harvest
harvest = json.load(open('harvested_all_dramas.json', 'r', encoding='utf-8'))

# Load Indonesian IDs from sorted file
indo_text = open('sorted_by_language/dramas_indonesian.txt', 'r', encoding='utf-8').read()
indo_ids = [m.group(1) for m in re.finditer(r'^\d+\s+(\d+)\s+', indo_text, re.M)]

# Process
clean_list = []
duplicates = []
false_positives = []

# Group by title for duplicate detection
title_groups = defaultdict(list)

for pid in indo_ids:
    if pid in existing_ids:
        continue
    if pid not in harvest:
        continue
    
    d = harvest[pid]
    title = d['title'].strip()
    eps = d['total_episodes']
    
    # False positive check
    if pid in FALSE_POSITIVE_IDS:
        false_positives.append((pid, title, eps, "false positive"))
        continue
    
    # Check if title already in Supabase (duplicate with different ID)
    if title.strip().lower() in existing_titles:
        duplicates.append((pid, title, eps, "judul sudah ada di DB"))
        continue
    
    # Check for dubbing versions
    base_title = re.sub(r'\s*[\(（]Dubbing[\)）]\s*$', '', title, flags=re.I).strip()
    if base_title.lower() != title.lower() and base_title.lower() in existing_titles:
        duplicates.append((pid, title, eps, f"versi dubbing dari '{base_title}'"))
        continue
    
    title_groups[title.lower()].append((pid, title, eps))

# Detect internal duplicates (same title, multiple IDs in new list)
for title_key, items in title_groups.items():
    if len(items) > 1:
        # Keep the one with most episodes
        items.sort(key=lambda x: -x[2])
        clean_list.append(items[0])
        for dup in items[1:]:
            duplicates.append((dup[0], dup[1], dup[2], f"duplikat internal, ID {items[0][0]} lebih lengkap"))
    else:
        clean_list.append(items[0])

# Sort by ID
clean_list.sort(key=lambda x: int(x[0]))

# Output
print("=" * 78)
print("  DRAMA INDONESIA BARU (BERSIH)")
print(f"  Total: {len(clean_list)} drama unik")
print("=" * 78)
print(f"\n{'No':>3}  {'ID':<6}  {'Judul':<55} {'Episode':>7}")
print("-" * 78)
for i, (pid, title, eps) in enumerate(clean_list, 1):
    print(f"{i:>3}. [{pid:<5}] {title:<55} {eps:>3} eps")

print(f"\n{'=' * 78}")
print(f"  DIBUANG: {len(false_positives)} false positive + {len(duplicates)} duplikat")
print(f"{'=' * 78}")

if false_positives:
    print(f"\n  False Positive ({len(false_positives)}):")
    for pid, title, eps, reason in false_positives:
        print(f"    ❌ [{pid}] {title[:45]} — {reason}")

if duplicates:
    print(f"\n  Duplikat ({len(duplicates)}):")
    for pid, title, eps, reason in duplicates:
        print(f"    🔁 [{pid}] {title[:45]} — {reason}")

# Save clean list to file
output = []
for pid, title, eps in clean_list:
    output.append({"id": pid, "title": title, "total_episodes": eps})

with open('new_indonesian_clean.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Daftar bersih disimpan ke: new_indonesian_clean.json")
