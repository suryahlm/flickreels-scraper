#!/usr/bin/env python3
"""
Sortir semua drama hasil harvest berdasarkan bahasa.
Output: file TXT terpisah per bahasa di folder sorted_by_language/
"""
import sys
sys.path.insert(0, '.')
import re
import json
import os
from pathlib import Path
from collections import defaultdict

HARVEST_FILE = "harvested_all_dramas.json"
OUTPUT_DIR = "sorted_by_language"

# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(title, language_name=""):
    """Deteksi bahasa dari judul + language_name field"""
    
    # 1. Jika language_name terisi, gunakan itu
    if language_name:
        lang = language_name.strip().lower()
        if lang:
            return lang.capitalize()
    
    # 2. Deteksi dari karakter judul
    
    # Chinese (Simplified & Traditional)
    if re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', title):
        # Cek apakah ada Hiragana/Katakana (campuran = Japanese)
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', title):
            return "Japanese"
        return "Chinese"
    
    # Japanese (Hiragana, Katakana)
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', title):
        return "Japanese"
    
    # Korean (Hangul)
    if re.search(r'[\uac00-\ud7af\u1100-\u11ff]', title):
        return "Korean"
    
    # Thai
    if re.search(r'[\u0e00-\u0e7f]', title):
        return "Thai"
    
    # Arabic
    if re.search(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]', title):
        return "Arabic"
    
    # Cyrillic (Russian)
    if re.search(r'[\u0400-\u04ff]', title):
        return "Russian"
    
    # --- Latin-based languages ---
    title_lower = title.lower()
    
    # Indonesian keywords
    indo_keywords = [
        r'\byang\b', r'\bdan\b', r'\bdari\b', r'\buntuk\b', r'\bdengan\b',
        r'\bpada\b', r'\boleh\b', r'\bagar\b', r'\btetapi\b', r'\bnamun\b',
        r'\bsudah\b', r'\bbelum\b', r'\bakan\b', r'\bmasih\b', r'\bjuga\b',
        r'\baku\b', r'\bkamu\b', r'\bkau\b', r'\bdia\b', r'\bkita\b',
        r'\bmereka\b', r'\bsaya\b', r'\bkami\b',
        r'ku\b', r'mu\b', r'nya\b',
        r'\bcinta\b', r'\bsayang\b', r'\bhati\b', r'\brindu\b', r'\bhidup\b',
        r'\btakdir\b', r'\brahasia\b', r'\bdendam\b', r'\bbalas\b',
        r'\bkembali\b', r'\btidak\b', r'\btak\b', r'\bbukan\b', r'\bjangan\b',
        r'\bmaaf\b', r'\btolong\b', r'\bmenawan\b', r'\bberikan\b',
        r'\bmenikah\b', r'\bbercerai\b', r'\bbertemu\b', r'\bbersinar\b',
        r'\bsuami\b', r'\bistri\b', r'\banak\b', r'\bibu\b', r'\bayah\b',
        r'\bpacar\b', r'\bmantan\b', r'\bkekasih\b', r'\bkeluarga\b',
        r'\bgadis\b', r'\bwanita\b', r'\bpria\b', r'\bpemuda\b',
        r'\bbos\b', r'\bpresiden\b', r'\bdirektur\b', r'\bkaisar\b',
        r'\bpangeran\b', r'\bputri\b', r'\bratu\b', r'\braja\b',
        r'\bpermaisuri\b', r'\btuan\b', r'\bnona\b', r'\bnyonya\b',
        r'\bpanglima\b', r'\bjenderal\b', r'\bpenjaga\b', r'\bperamal\b',
        r'\bgodaan\b', r'\bpesona\b', r'\bwarisan\b', r'\bmisteri\b',
        r'\bmalam\b', r'\bdunia\b', r'\bkeadilan\b', r'\bkekuatan\b',
        r'\bnaga\b', r'\bdewa\b', r'\bbidadari\b', r'\bsimpan\b',
        r'\bmawar\b', r'\bduri\b', r'\bcahaya\b', r'\bdebu\b',
        r'\blewat\b', r'\bbaru\b', r'\btinggi\b', r'\bsang\b',
        r'\bsi\b', r'\bpara\b', r'\bini\b', r'\bitu\b',
        r'\bterlalu\b', r'\bsangat\b', r'\bsekali\b', r'\bpergi\b',
        r'\bdapat\b', r'\bmenjadi\b', r'\bmencari\b', r'\bmencuri\b',
        r'\bselamat\b', r'\btinggal\b', r'\bjatuh\b', r'\bbangkit\b',
        r'\bpertama\b', r'\bkedua\b', r'\bketiga\b', r'\bterakhir\b',
        r'\bkehidupan\b', r'\bpembunuhan\b', r'\bperjuangan\b',
        r'\bpengkhianatan\b', r'\bpengorbanan\b', r'\bkeajaiban\b',
        r'\brumah\b', r'\btempat\b', r'\bjalan\b', r'\bpintu\b',
        r'\bmata\b', r'\bbibir\b', r'\btangan\b', r'\bdaun\b',
        r'\bketika\b', r'\bsetelah\b', r'\bsebelum\b', r'\bsejak\b',
        r'\bsebagai\b', r'\bbegitu\b', r'\bsedang\b',
    ]
    if re.search("|".join(indo_keywords), title_lower):
        return "Indonesian"
    
    # Spanish
    spanish_markers = [r'[áéíóúñ¿¡]', r'\bel\b', r'\bla\b', r'\bdel\b', r'\blos\b', r'\blas\b', 
                       r'\bpor\b', r'\bcon\b', r'\buna\b', r'\bmí\b', r'\bque\b', r'\bcorazón\b',
                       r'\bamor\b', r'\bvida\b', r'\bmujer\b', r'\bhombre\b']
    if re.search("|".join(spanish_markers), title_lower):
        return "Spanish"
    
    # French
    french_markers = [r'\ble\b', r'\bla\b', r'\bles\b', r'\bdes\b', r'\bmon\b', r'\bma\b',
                      r'\bmes\b', r'\bune\b', r'\bpour\b', r'\bavec\b', r'\bdans\b',
                      r'\best\b', r'\bqui\b', r'\bcoeur\b', r'[àâçéèêëîïôùûü]', r"l'", r"d'"]
    if re.search("|".join(french_markers), title_lower):
        return "French"
    
    # Portuguese
    portuguese_markers = [r'[ãõçâêô]', r'\bcom\b', r'\bnão\b', r'\bpara\b', r'\buma\b',
                          r'\bmeu\b', r'\bminha\b', r'\bseu\b', r'\bsua\b', r'\bcoração\b',
                          r'\bamor\b', r'\bvida\b']
    if re.search("|".join(portuguese_markers), title_lower):
        return "Portuguese"
    
    # German
    german_markers = [r'[äöüß]', r'\bder\b', r'\bdie\b', r'\bdas\b', r'\bein\b', r'\beine\b',
                      r'\bund\b', r'\bmein\b', r'\bmeine\b', r'\bist\b', r'\bnicht\b',
                      r'\bmir\b', r'\bliebe\b', r'\bherz\b']
    if re.search("|".join(german_markers), title_lower):
        return "German"
    
    # Default: jika murni Latin tanpa aksen dan tidak match apapun = English
    return "English"


def main():
    # Load harvest data
    if not Path(HARVEST_FILE).exists():
        print(f"ERROR: {HARVEST_FILE} not found. Run harvest_all_ids.py first!")
        return
    
    with open(HARVEST_FILE, "r", encoding="utf-8") as f:
        harvested = json.load(f)
    
    print(f"Loaded {len(harvested)} dramas from harvest")
    
    # Classify by language
    by_language = defaultdict(list)
    
    for pid, drama in sorted(harvested.items(), key=lambda x: int(x[0])):
        title = drama.get("title", "")
        lang_field = drama.get("language_name", "")
        detected_lang = detect_language(title, lang_field)
        
        by_language[detected_lang].append({
            "id": pid,
            "title": title,
            "episodes": drama.get("total_episodes", 0),
            "language_field": lang_field
        })
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Summary
    print(f"\n{'=' * 70}")
    print(f"HASIL SORTIR BAHASA")
    print(f"{'=' * 70}")
    print(f"{'Bahasa':<20} {'Jumlah':>8}  {'File'}")
    print(f"{'-' * 60}")
    
    total = 0
    for lang in sorted(by_language.keys(), key=lambda x: -len(by_language[x])):
        dramas = by_language[lang]
        total += len(dramas)
        
        # Create TXT file
        filename = f"dramas_{lang.lower().replace(' ', '_')}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{'=' * 70}\n")
            f.write(f"  DAFTAR DRAMA - {lang.upper()}\n")
            f.write(f"  Total: {len(dramas)} drama\n")
            f.write(f"{'=' * 70}\n\n")
            f.write(f"{'No.':<6} {'ID':<8} {'Judul':<50} {'Episode':>8}\n")
            f.write(f"{'-' * 75}\n")
            
            for i, d in enumerate(dramas, 1):
                title_display = d['title'][:48]
                f.write(f"{i:<6} {d['id']:<8} {title_display:<50} {d['episodes']:>5} eps\n")
            
            f.write(f"\n{'-' * 75}\n")
            f.write(f"Total: {len(dramas)} drama\n")
        
        print(f"  {lang:<20} {len(dramas):>5}    {filename}")
    
    print(f"{'-' * 60}")
    print(f"  {'TOTAL':<20} {total:>5}")
    print(f"\nFile disimpan di: {os.path.abspath(OUTPUT_DIR)}/")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
