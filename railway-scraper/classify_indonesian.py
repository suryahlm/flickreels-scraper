#!/usr/bin/env python3
"""
Indonesian Drama Classifier
=============================
Post-processing script to classify harvested dramas into Indonesian/non-Indonesian
using hybrid regex title detection (karena language_name field kosong).

Usage:
    python classify_indonesian.py                    # Classify harvested data
    python classify_indonesian.py --scrape=5         # Classify + scrape top 5 new
"""
import sys
sys.path.insert(0, '.')
import re
import json
import argparse
import logging
from pathlib import Path
from local_scraping_indonesia import LocalIndonesianScraper, SUPABASE_CONFIG
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('classify.log', encoding='utf-8')
    ]
)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

HARVEST_FILE = "harvested_all_dramas.json"
CLASSIFIED_FILE = "classified_indonesian.json"


def is_likely_indonesian(title):
    """
    Deteksi bahasa Indonesia dari judul drama.
    Hybrid approach: Block non-Latin chars + Keyword whitelist.
    """
    # 1. Block karakter asing (CJK, Hangul, Thai, Cyrillic, Arabic)
    if re.search(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0e00-\u0e7f\u0400-\u04ff\u0600-\u06ff]', title):
        return False

    title_lower = title.lower()

    # 2. Block bahasa lain yang pakai Latin (Spanish, French, Portuguese, German)
    # Jika ada karakter aksen yang BUKAN bahasa Indonesia
    non_indo_accents = re.search(r'[àáâãäåæçèéêëìíîïñòóôõöùúûüýÿœ¿¡ß]', title_lower)
    # Indonesia sangat jarang pakai aksen, kecuali nama daerah
    
    # 3. Whitelist kata kunci Indonesia (regex word boundary)
    indo_keywords = [
        # Partikel & Konjungsi
        r'\byang\b', r'\bdan\b', r'\bdari\b', r'\buntuk\b', r'\bdengan\b',
        r'\bpada\b', r'\boleh\b', r'\bsebagai\b', r'\bagar\b', r'\bbahwa\b',
        r'\btetapi\b', r'\bnamun\b', r'\bsedang\b', r'\bsudah\b', r'\bbelum\b',
        r'\bakan\b', r'\btelah\b', r'\bmasih\b', r'\bjuga\b', r'\bsangat\b',

        # Kata Ganti
        r'\baku\b', r'\bkamu\b', r'\bkau\b', r'\bdia\b', r'\bkita\b',
        r'\bmereka\b', r'\bsaya\b', r'\bkami\b', r'\bandai\b',

        # Suffix umum (-ku, -mu, -nya)
        r'ku\b', r'mu\b', r'nya\b',

        # Kata Sifat/Kerja umum
        r'\bcinta\b', r'\bsayang\b', r'\bhati\b', r'\brindu\b', r'\bhidup\b',
        r'\bmati\b', r'\btakdir\b', r'\brahasia\b', r'\bdendam\b', r'\bbalas\b',
        r'\bkembali\b', r'\bpergi\b', r'\bdatang\b', r'\btahu\b', r'\bbisa\b',
        r'\btidak\b', r'\btak\b', r'\bbukan\b', r'\bjangan\b', r'\bmaaf\b',
        r'\btolong\b', r'\bmencuri\b', r'\bmencari\b', r'\bmenang\b',
        r'\bbersinar\b', r'\bbegitu\b', r'\bmenawan\b', r'\bberikan\b',
        r'\btersembunyi\b', r'\bmenikah\b', r'\bbercerai\b', r'\bbertemu\b',

        # Keluarga & Hubungan
        r'\bsuami\b', r'\bistri\b', r'\banak\b', r'\bibu\b', r'\bayah\b',
        r'\bpacar\b', r'\bmantan\b', r'\bkekasih\b', r'\bkeluarga\b',
        r'\bgadis\b', r'\bwanita\b', r'\bpria\b', r'\bpemuda\b',

        # Jabatan & Status
        r'\bbos\b', r'\bpresiden\b', r'\bdirektur\b', r'\bkaisar\b',
        r'\bpangeran\b', r'\bputri\b', r'\bratu\b', r'\braja\b',
        r'\bpermaisuri\b', r'\btuan\b', r'\bnona\b', r'\bnyonya\b',
        r'\bpanglima\b', r'\bjenderal\b', r'\bpenjaga\b', r'\bperamal\b',

        # Kata umum drama
        r'\bgodaan\b', r'\bpesona\b', r'\bwarisan\b', r'\bmisteri\b',
        r'\bmalam\b', r'\bdunia\b', r'\bkehidupan\b', r'\bkeadilan\b',
        r'\bkekuatan\b', r'\bkebangkitan\b', r'\bpembunuhan\b',
        r'\bpertarungan\b', r'\bperjuangan\b', r'\bkemenangan\b',
        r'\bpengkhianatan\b', r'\bpengorbanan\b', r'\bkeajaiban\b',

        # Kata benda umum 
        r'\bnaga\b', r'\bdewa\b', r'\bbidadari\b', r'\bsimpan\b',
        r'\bmawar\b', r'\bduri\b', r'\bcahaya\b', r'\bdebu\b',
        r'\bpintu\b', r'\bjalan\b', r'\btempat\b', r'\brumah\b',
        r'\blewat\b', r'\bbaru\b', r'\blama\b', r'\btinggi\b',
    ]

    # Gabung jadi satu regex raksasa
    regex_pattern = "|".join(indo_keywords)
    if re.search(regex_pattern, title_lower):
        return True

    # 4. Jika ada aksen non-Indo dan tidak match keyword
    if non_indo_accents:
        return False

    # 5. Fallback: cek apakah pakai huruf Latin murni tanpa match apapun
    # Ini bisa English, Portuguese, dll — JANGAN ambil tanpa bukti
    return False


def main():
    parser = argparse.ArgumentParser(description="Classify Indonesian Dramas")
    parser.add_argument("--scrape", type=int, default=0, help="Scrape N new Indonesian dramas")
    args = parser.parse_args()

    # Load harvested data
    if not Path(HARVEST_FILE).exists():
        logger.error(f"No harvest file found: {HARVEST_FILE}")
        logger.error("Run harvest_all_ids.py first!")
        return

    with open(HARVEST_FILE, "r", encoding="utf-8") as f:
        harvested = json.load(f)

    logger.info(f"Loaded {len(harvested)} harvested dramas")

    # Load existing Supabase IDs (already scraped)
    resp = requests.get(
        f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
        headers={"apikey": SUPABASE_CONFIG["key"]}
    )
    existing_ids = set()
    if resp.status_code == 200:
        for d in resp.json():
            if d.get('flickreels_id'):
                existing_ids.add(str(d['flickreels_id']))
    logger.info(f"Already in Supabase: {len(existing_ids)}")

    # Classify
    indonesian = []
    non_indonesian = []
    already_have = []

    for pid, drama in harvested.items():
        title = drama.get("title", "")
        lang = drama.get("language_name", "")

        if pid in existing_ids:
            already_have.append(drama)
            continue

        # Check language_name field first (if available)
        if lang and ("indonesian" in lang.lower() or "indonesia" in lang.lower()):
            indonesian.append(drama)
            continue

        # Use title-based detection
        if is_likely_indonesian(title):
            indonesian.append(drama)
        else:
            non_indonesian.append(drama)

    # Report
    logger.info(f"\n{'=' * 60}")
    logger.info("CLASSIFICATION RESULTS")
    logger.info(f"{'=' * 60}")
    logger.info(f"  Total harvested: {len(harvested)}")
    logger.info(f"  Already in Supabase: {len(already_have)}")
    logger.info(f"  🇮🇩 Indonesian (NEW): {len(indonesian)}")
    logger.info(f"  🌍 Non-Indonesian: {len(non_indonesian)}")

    if indonesian:
        logger.info(f"\n  New Indonesian dramas:")
        for drama in sorted(indonesian, key=lambda x: int(x['id'])):
            lang_tag = f" [{drama['language_name']}]" if drama['language_name'] else ""
            logger.info(f"    [{drama['id']}] {drama['title'][:50]}{lang_tag} ({drama['total_episodes']} eps)")

        # Save classified results
        with open(CLASSIFIED_FILE, "w", encoding="utf-8") as f:
            json.dump(indonesian, f, ensure_ascii=False, indent=2)
        logger.info(f"\n  Saved to {CLASSIFIED_FILE}")

    # Scrape if requested
    if args.scrape and indonesian:
        limit = min(args.scrape, len(indonesian))
        scraper = LocalIndonesianScraper()

        logger.info(f"\n{'=' * 60}")
        logger.info(f"SCRAPING {limit} new Indonesian dramas")
        logger.info(f"{'=' * 60}\n")

        success = 0
        for drama in indonesian[:limit]:
            drama_info = {
                "id": drama["id"],
                "title": drama["title"],
                "cover": drama.get("cover", ""),
                "total_episodes": drama["total_episodes"],
                "description": "",
                "tags": []
            }
            logger.info(f"\n[{success + 1}/{limit}] {drama['title']} (ID: {drama['id']})")
            if scraper.scrape_drama(drama_info):
                success += 1
                logger.info(f"✅ SUCCESS ({success}/{limit})")
            else:
                logger.warning(f"⚠️ SKIPPED/FAILED")

            if success >= limit:
                break

        logger.info(f"\n{'=' * 60}")
        logger.info(f"SCRAPING COMPLETE: {success}/{limit}")
        logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
