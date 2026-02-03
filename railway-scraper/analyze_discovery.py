#!/usr/bin/env python3
"""
Script untuk menganalisa kelengkapan data 451 drama Indonesia dari discovery
dan membandingkan dengan data yang sudah ada di app.
"""

import json
from pathlib import Path

def main():
    # Load discovered dramas
    discovery_file = Path("discovered_indonesia.json")
    existing_file = Path(r"D:\Surya\IT\AsianDrama-02\assets\data\dramas.json")
    
    print("=" * 60)
    print("ANALISA KELENGKAPAN DATA DRAMA INDONESIA")
    print("=" * 60)
    
    # Load discovery data
    with open(discovery_file, 'r', encoding='utf-8') as f:
        discovered = json.load(f)
    
    print(f"\n📦 Total drama dari discovery: {len(discovered)}")
    
    # Analisa kelengkapan
    complete = 0
    missing_cover = []
    missing_episodes = []
    empty_episodes = []
    incomplete = []
    
    for drama in discovered:
        drama_id = drama.get('id', 'N/A')
        title = drama.get('title', 'N/A')
        cover = drama.get('cover', '')
        total_eps = drama.get('total_episodes', 0)
        episodes = drama.get('episodes', [])
        
        issues = []
        
        # Cek cover
        if not cover or cover.strip() == '':
            issues.append("cover kosong")
            missing_cover.append({'id': drama_id, 'title': title})
        
        # Cek episodes
        if not episodes or len(episodes) == 0:
            issues.append("episodes kosong")
            empty_episodes.append({'id': drama_id, 'title': title, 'total_episodes': total_eps})
        elif len(episodes) != total_eps:
            issues.append(f"episodes tidak lengkap ({len(episodes)}/{total_eps})")
            missing_episodes.append({
                'id': drama_id, 
                'title': title, 
                'actual': len(episodes), 
                'expected': total_eps
            })
        
        if issues:
            incomplete.append({'id': drama_id, 'title': title, 'issues': issues})
        else:
            complete += 1
    
    print(f"\n✅ Drama dengan data LENGKAP: {complete}")
    print(f"❌ Drama dengan data TIDAK LENGKAP: {len(incomplete)}")
    
    if missing_cover:
        print(f"\n⚠️  Drama tanpa cover: {len(missing_cover)}")
        for d in missing_cover[:5]:
            print(f"   - [{d['id']}] {d['title']}")
        if len(missing_cover) > 5:
            print(f"   ... dan {len(missing_cover) - 5} lainnya")
    
    if empty_episodes:
        print(f"\n⚠️  Drama dengan episodes kosong: {len(empty_episodes)}")
        for d in empty_episodes[:5]:
            print(f"   - [{d['id']}] {d['title']} (expected: {d['total_episodes']} eps)")
        if len(empty_episodes) > 5:
            print(f"   ... dan {len(empty_episodes) - 5} lainnya")
    
    if missing_episodes:
        print(f"\n⚠️  Drama dengan episodes tidak lengkap: {len(missing_episodes)}")
        for d in missing_episodes[:5]:
            print(f"   - [{d['id']}] {d['title']} ({d['actual']}/{d['expected']} eps)")
        if len(missing_episodes) > 5:
            print(f"   ... dan {len(missing_episodes) - 5} lainnya")
    
    # Load existing dramas dari app
    print("\n" + "=" * 60)
    print("PERBANDINGAN DENGAN DATA DI APP")
    print("=" * 60)
    
    with open(existing_file, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    
    print(f"\n📱 Total drama di app: {len(existing)}")
    
    # Buat set ID untuk perbandingan
    discovered_ids = set(d['id'] for d in discovered)
    existing_ids = set(d['id'] for d in existing)
    
    # Drama yang sudah ada di kedua tempat
    overlap_ids = discovered_ids & existing_ids
    # Drama di discovery tapi belum di app
    new_ids = discovered_ids - existing_ids
    # Drama di app tapi tidak di discovery
    only_in_app = existing_ids - discovered_ids
    
    print(f"\n🔄 Drama yang SUDAH ADA di app (overlap): {len(overlap_ids)}")
    if overlap_ids:
        # Cari judul dari discovered
        overlap_dramas = [d for d in discovered if d['id'] in overlap_ids]
        for d in sorted(overlap_dramas, key=lambda x: x['title'])[:20]:
            print(f"   ✓ [{d['id']}] {d['title']}")
        if len(overlap_ids) > 20:
            print(f"   ... dan {len(overlap_ids) - 20} lainnya")
    
    print(f"\n🆕 Drama BARU (di discovery tapi belum di app): {len(new_ids)}")
    if new_ids:
        new_dramas = [d for d in discovered if d['id'] in new_ids]
        for d in sorted(new_dramas, key=lambda x: x['title'])[:10]:
            print(f"   + [{d['id']}] {d['title']} ({d['total_episodes']} eps)")
        if len(new_ids) > 10:
            print(f"   ... dan {len(new_ids) - 10} lainnya")
    
    print(f"\n❓ Drama di APP tapi tidak di discovery: {len(only_in_app)}")
    if only_in_app:
        only_app_dramas = [d for d in existing if d['id'] in only_in_app]
        for d in sorted(only_app_dramas, key=lambda x: x['title']):
            print(f"   ? [{d['id']}] {d['title']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("RINGKASAN")
    print("=" * 60)
    print(f"\n📊 Total dari discovery: {len(discovered)}")
    print(f"   - Data lengkap: {complete}")
    print(f"   - Data tidak lengkap: {len(incomplete)}")
    print(f"\n📱 Total di app saat ini: {len(existing)}")
    print(f"   - Sudah ada di discovery juga: {len(overlap_ids)}")
    print(f"   - Hanya di app (tidak di discovery): {len(only_in_app)}")
    print(f"\n🆕 Drama baru yang bisa ditambahkan: {len(new_ids)}")
    
    # Simpan hasil analisa ke JSON
    analysis = {
        "discovery_total": len(discovered),
        "complete_data": complete,
        "incomplete_data": len(incomplete),
        "missing_cover_count": len(missing_cover),
        "empty_episodes_count": len(empty_episodes),
        "missing_episodes_count": len(missing_episodes),
        "app_total": len(existing),
        "overlap_count": len(overlap_ids),
        "new_dramas_count": len(new_ids),
        "only_in_app_count": len(only_in_app),
        "overlap_ids": list(overlap_ids),
        "new_ids": list(new_ids),
        "only_in_app_ids": list(only_in_app),
        "missing_cover": missing_cover,
        "empty_episodes": empty_episodes,
        "missing_episodes": missing_episodes
    }
    
    with open("analysis_result.json", 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Hasil analisa disimpan ke: analysis_result.json")

if __name__ == "__main__":
    main()
