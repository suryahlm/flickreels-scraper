#!/usr/bin/env python3
"""
Scrape 77 Drama Indonesia Baru (dari harvest brute-force ID scan)
=================================================================
Membaca daftar dari new_indonesian_clean.json, scrape video + upload R2 + Supabase.

Reuses infrastructure dari batch_scraper_indonesia.py:
  - IndonesianAPI (chapterList, play)
  - R2Uploader (segment + manifest upload)
  - SupabaseClient (upsert drama metadata)

Usage:
    python scrape_new_77.py              # Scrape semua 77 drama
    python scrape_new_77.py --limit=5    # Test 5 drama dulu
    python scrape_new_77.py --dry-run    # Cek list tanpa scrape
"""
import os
import sys
import json
import time
import logging
import argparse

# Import everything from batch_scraper_indonesia
from batch_scraper_indonesia import (
    IndonesianAPI, R2Uploader, SupabaseClient,
    SUPABASE_CONFIG, CONCURRENT_CONFIG,
    IndonesianBatchScraper
)

import requests

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# JSON file with clean drama list
DRAMA_LIST_FILE = "new_indonesian_clean.json"


def load_drama_list():
    """Load drama list dari new_indonesian_clean.json"""
    if not os.path.exists(DRAMA_LIST_FILE):
        logger.error(f"File {DRAMA_LIST_FILE} tidak ditemukan!")
        sys.exit(1)
    
    with open(DRAMA_LIST_FILE, "r", encoding="utf-8") as f:
        dramas = json.load(f)
    
    logger.info(f"Loaded {len(dramas)} dramas dari {DRAMA_LIST_FILE}")
    return dramas


def load_existing_ids():
    """Load drama IDs yang sudah ada di Supabase"""
    try:
        resp = requests.get(
            f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
            headers={"apikey": SUPABASE_CONFIG["key"]}
        )
        if resp.status_code == 200:
            ids = set(str(d['flickreels_id']) for d in resp.json() if d.get('flickreels_id'))
            logger.info(f"Found {len(ids)} existing dramas in Supabase")
            return ids
    except Exception as e:
        logger.warning(f"Error loading existing IDs: {e}")
    return set()


def main():
    parser = argparse.ArgumentParser(description="Scrape 77 Drama Indonesia Baru")
    parser.add_argument("--limit", type=int, default=None, help="Limit jumlah drama")
    parser.add_argument("--dry-run", action="store_true", help="Hanya tampilkan list, tanpa scrape")
    args = parser.parse_args()
    
    # Load drama list
    dramas = load_drama_list()
    
    # Load existing IDs
    existing_ids = load_existing_ids()
    
    # Filter yang sudah ada
    new_dramas = [d for d in dramas if str(d["id"]) not in existing_ids]
    logger.info(f"Drama baru (belum di Supabase): {len(new_dramas)}")
    
    if not new_dramas:
        logger.info("Semua drama sudah ada di Supabase! Tidak ada yang perlu di-scrape.")
        return
    
    # Apply limit
    if args.limit:
        new_dramas = new_dramas[:args.limit]
        logger.info(f"Dibatasi ke {args.limit} drama")
    
    # Dry run mode
    if args.dry_run:
        logger.info(f"\n{'='*60}")
        logger.info("DRY RUN - Daftar drama yang akan di-scrape:")
        logger.info(f"{'='*60}")
        for i, d in enumerate(new_dramas, 1):
            logger.info(f"  {i:>3}. [{d['id']}] {d['title']} ({d['total_episodes']} eps)")
        logger.info(f"\nTotal: {len(new_dramas)} drama")
        return
    
    # Real scraping
    logger.info(f"\n{'='*60}")
    logger.info(f"SCRAPING {len(new_dramas)} DRAMA INDONESIA BARU")
    logger.info(f"{'='*60}\n")
    
    # Use the existing IndonesianBatchScraper
    scraper = IndonesianBatchScraper()
    
    start_time = time.time()
    success_count = 0
    fail_count = 0
    
    for i, drama_info in enumerate(new_dramas):
        drama_id = str(drama_info["id"])
        title = drama_info["title"]
        
        logger.info(f"\n[{i+1}/{len(new_dramas)}] {title} (ID: {drama_id})")
        
        # Skip if already scraped (double-check)
        if drama_id in scraper.scraped_ids:
            logger.info(f"  ⏭️ Sudah ada, skip")
            continue
        
        # Get full metadata from API (chapterList provides cover, episodes, etc.)
        detail = scraper.api.get_drama_detail(drama_id)
        if not detail or not detail.get("episodes"):
            logger.error(f"  ❌ Gagal ambil detail drama")
            fail_count += 1
            continue
        
        # Build drama dict compatible with scraper.scrape_drama()
        drama = {
            "id": drama_id,
            "title": detail.get("title", title),  # Prefer API title
            "cover": detail.get("cover", ""),
            "description": "",
            "total_episodes": len(detail["episodes"]),
            "tags": []
        }
        
        try:
            scraper.scrape_drama(drama)
            success_count += 1
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            fail_count += 1
    
    # Final report
    elapsed = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"SCRAPING SELESAI!")
    logger.info(f"  Sukses:  {success_count}")
    logger.info(f"  Gagal:   {fail_count}")
    logger.info(f"  Skipped: {len(new_dramas) - success_count - fail_count}")
    logger.info(f"  Waktu:   {elapsed/60:.1f} menit")
    if success_count > 0:
        logger.info(f"  Rata-rata: {elapsed/60/success_count:.1f} min/drama")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
