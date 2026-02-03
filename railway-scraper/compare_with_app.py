#!/usr/bin/env python3
"""
Script untuk menganalisa 451 drama discovery vs 42 drama di app (WORKING_DRAMA_IDS)
"""

import json
from pathlib import Path

def main():
    # Load discovered dramas
    discovery_file = Path("discovered_indonesia.json")
    
    print("=" * 60)
    print("PERBANDINGAN: 451 DISCOVERY vs 42 DI APP")
    print("=" * 60)
    
    # Load discovery data
    with open(discovery_file, 'r', encoding='utf-8') as f:
        discovered = json.load(f)
    
    print(f"\n📦 Total drama dari discovery: {len(discovered)}")
    
    # 42 drama IDs yang sudah ada di app (dari r2DramaService.ts)
    WORKING_DRAMA_IDS = {
        '894', '5190', '5136', '3108', '5119', '721', '978', '5194', '5122', '487', '5071', '4009',
        '3495', '5137', '495', '977', '5235', '5202', '963', '5089', '5159', '3985', '4464', '4784',
        '533', '5135', '2186', '3674', '4187', '4158', '2518', '5220', '5031', '5247', '5099', '4511',
        '4839', '5043', '3164', '5226', '2858', '1445',
    }
    
    print(f"📱 Total drama di app (WORKING_DRAMA_IDS): {len(WORKING_DRAMA_IDS)}")
    
    # Buat set ID discovery
    discovered_ids = set(d['id'] for d in discovered)
    
    # Analisa perbandingan
    overlap_ids = discovered_ids & WORKING_DRAMA_IDS
    new_ids = discovered_ids - WORKING_DRAMA_IDS
    only_in_app = WORKING_DRAMA_IDS - discovered_ids
    
    print(f"\n🔄 Drama yang ada di KEDUA tempat (overlap): {len(overlap_ids)}")
    
    # Tampilkan drama overlap
    overlap_dramas = [d for d in discovered if d['id'] in overlap_ids]
    print("\nDrama yang sudah ada di app DAN discovery:")
    for d in sorted(overlap_dramas, key=lambda x: x['title']):
        print(f"   ✓ [{d['id']}] {d['title']} ({d['total_episodes']} eps)")
    
    print(f"\n🆕 Drama BARU (di discovery tapi BELUM di app): {len(new_ids)}")
    
    # Hitung statistik drama baru
    new_dramas = [d for d in discovered if d['id'] in new_ids]
    total_new_episodes = sum(d['total_episodes'] for d in new_dramas)
    
    print(f"   Total episode baru: {total_new_episodes:,}")
    print(f"\n   Contoh drama baru:")
    for d in sorted(new_dramas, key=lambda x: x['title'])[:15]:
        print(f"   + [{d['id']}] {d['title']} ({d['total_episodes']} eps)")
    print(f"   ... dan {len(new_ids) - 15} lainnya")
    
    print(f"\n❓ Drama di APP tapi TIDAK di discovery: {len(only_in_app)}")
    if only_in_app:
        print(f"   IDs: {sorted(only_in_app)}")
    
    # Simpan hasil
    print("\n" + "=" * 60)
    print("RINGKASAN")
    print("=" * 60)
    print(f"\n📊 Total dari discovery: {len(discovered)}")
    print(f"📱 Total di app saat ini: {len(WORKING_DRAMA_IDS)}")
    print(f"🔄 Overlap (sudah ada): {len(overlap_ids)}")
    print(f"🆕 Drama baru yang bisa ditambahkan: {len(new_ids)}")
    print(f"📺 Total episode baru: {total_new_episodes:,}")
    
    # Simpan list drama baru ke file
    new_dramas_export = sorted(new_dramas, key=lambda x: x['title'])
    with open("new_dramas_for_app.json", 'w', encoding='utf-8') as f:
        json.dump(new_dramas_export, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 List drama baru disimpan ke: new_dramas_for_app.json")

if __name__ == "__main__":
    main()
