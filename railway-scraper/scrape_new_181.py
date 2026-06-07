#!/usr/bin/env python3
"""
Scrape 181 NEW Indonesian Dramas from Known IDs
==================================================
Uses the drama IDs discovered in new_dramas_list.txt
which we verified can be fetched via chapterList API.

This script:
1. Reads the 181 new drama IDs from new_dramas_list.txt
2. Fetches episode details for each
3. Downloads HLS streams to R2
4. Saves to Supabase

Usage:
    python scrape_new_181.py                # Scrape all
    python scrape_new_181.py --limit=5      # Test with 5 dramas
    python scrape_new_181.py --start=50     # Start from drama #50
"""
import re
import sys
import argparse
import logging

# Import the main scraper class
from batch_scraper_indonesia import IndonesianBatchScraper, IndonesianAPI, logger

def parse_new_dramas_list():
    """Parse new_dramas_list.txt to extract drama IDs and titles"""
    dramas = []
    try:
        with open("new_dramas_list.txt", "r", encoding="utf-8") as f:
            for line in f:
                # Match lines like: "  1. [  376] Menikah lagi dengan Ketua Direksi"
                match = re.search(r'\[\s*(\d+)\]\s+(.+)$', line.strip())
                if match:
                    drama_id = match.group(1)
                    title = match.group(2).strip()
                    dramas.append({
                        "id": drama_id,
                        "title": title,
                        "cover": "",  # Will be fetched from API
                        "description": "",
                        "tags": []
                    })
    except FileNotFoundError:
        logger.error("new_dramas_list.txt not found!")
        return []
    
    return dramas

def main():
    parser = argparse.ArgumentParser(description="Scrape 181 New Indonesian Dramas")
    parser.add_argument("--limit", type=int, default=None, help="Limit dramas to scrape")
    parser.add_argument("--start", type=int, default=0, help="Start from drama number (0-indexed)")
    args = parser.parse_args()
    
    # Parse the list
    dramas = parse_new_dramas_list()
    logger.info(f"Parsed {len(dramas)} dramas from new_dramas_list.txt")
    
    if not dramas:
        logger.error("No dramas found to scrape!")
        return
    
    # Create scraper
    scraper = IndonesianBatchScraper()
    api = IndonesianAPI()
    
    # Filter already scraped
    to_scrape = [d for d in dramas if d["id"] not in scraper.scraped_ids]
    logger.info(f"Already scraped: {len(dramas) - len(to_scrape)}")
    logger.info(f"New to scrape: {len(to_scrape)}")
    
    # Apply start and limit
    if args.start > 0:
        to_scrape = to_scrape[args.start:]
        logger.info(f"Starting from drama #{args.start}")
    
    if args.limit:
        to_scrape = to_scrape[:args.limit]
        logger.info(f"Limited to {len(to_scrape)} dramas")
    
    logger.info("=" * 60)
    logger.info("SCRAPING 181 NEW INDONESIAN DRAMAS")
    logger.info("=" * 60)
    
    # Scrape each drama
    for i, drama in enumerate(to_scrape, 1):
        logger.info(f"\n[{i}/{len(to_scrape)}] {drama['title']} (ID: {drama['id']})")
        
        # Fetch cover URL from detail API
        try:
            detail = api.get_drama_detail(drama['id'])
            if detail and detail.get('cover'):
                drama['cover'] = detail['cover']
                logger.info(f"  Cover: {drama['cover'][:50]}...")
        except Exception as e:
            logger.warning(f"  Could not fetch cover: {e}")
        
        # Scrape the drama
        scraper.scrape_drama(drama)
    
    # Final report
    logger.info("\n" + "=" * 60)
    logger.info("SCRAPING COMPLETE!")
    logger.info(f"  Processed: {len(to_scrape)} dramas")
    logger.info(f"  Episodes uploaded: {scraper.stats['episodes_uploaded']}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
