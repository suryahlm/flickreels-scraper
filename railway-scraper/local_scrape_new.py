#!/usr/bin/env python3
"""
LOCAL Indonesian Drama Scraper - Uses discovered 181 new dramas
==================================================================
Run from local machine to save Railway costs!

Usage:
    python local_scrape_new.py              # Scrape all 181 new dramas
    python local_scrape_new.py --limit=5    # Test with 5 dramas
"""
import sys
sys.path.insert(0, '.')
import json
import argparse
from batch_scraper_indonesia import IndonesianBatchScraper, logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help="Limit dramas to scrape")
    args = parser.parse_args()
    
    # Load discovered dramas
    with open("comprehensive_dramas.json", "r", encoding="utf-8") as f:
        discovered = json.load(f)
    
    # Create scraper (this loads existing IDs from Supabase)
    scraper = IndonesianBatchScraper()
    
    # Filter to only new dramas
    new_dramas = [d for d in discovered if str(d['id']) not in scraper.scraped_ids]
    
    logger.info("="*60)
    logger.info("LOCAL SCRAPER - 181 NEW DRAMAS")
    logger.info("="*60)
    logger.info(f"Discovered: {len(discovered)}")
    logger.info(f"Already scraped: {len(scraper.scraped_ids)}")
    logger.info(f"New to scrape: {len(new_dramas)}")
    
    if args.limit:
        new_dramas = new_dramas[:args.limit]
        logger.info(f"Limited to: {len(new_dramas)}")
    
    # Scrape each
    for i, drama in enumerate(new_dramas, 1):
        logger.info(f"\n[{i}/{len(new_dramas)}] {drama.get('title', 'N/A')}")
        scraper.scrape_drama(drama)
    
    # Report
    logger.info("\n" + "="*60)
    logger.info("COMPLETE!")
    logger.info(f"Processed: {len(new_dramas)} dramas")
    logger.info("="*60)

if __name__ == "__main__":
    main()
