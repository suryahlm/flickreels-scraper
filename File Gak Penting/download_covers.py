"""
Download cover images for dramas that already have videos downloaded.
Reads cover_url from metadata.json in each drama folder.
"""

import json
import os
from pathlib import Path
import requests

BASE_DIR = Path("D:/Surya/IT/Test Scraping/FlickReels/Video Drama TS/30.01.2026")
USER_AGENT = "FlickReels/2.2.3.0 (Android 13; en)"

def download_covers():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    # Also load cover URLs from scraped data
    scraped_data = {}
    scraped_file = Path("D:/Surya/IT/Test Scraping/FlickReels/Scraping 01/30.01.2026/dramas.json")
    if scraped_file.exists():
        with open(scraped_file, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
    
    for drama_folder in BASE_DIR.iterdir():
        if not drama_folder.is_dir():
            continue
            
        cover_path = drama_folder / "cover.jpg"
        if cover_path.exists():
            print(f"[SKIP] {drama_folder.name} - cover exists")
            continue
        
        # Try to get cover_url from metadata.json
        meta_path = drama_folder / "metadata.json"
        cover_url = None
        
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                cover_url = meta.get("cover_url", "")
        
        # If not in metadata, try scraped data
        if not cover_url:
            # Extract ID from folder name like "Title (ID)"
            folder_name = drama_folder.name
            if "(" in folder_name and ")" in folder_name:
                drama_id = folder_name.rsplit("(", 1)[1].rstrip(")")
                if drama_id in scraped_data:
                    cover_url = scraped_data[drama_id].get("cover_url", "")
        
        if not cover_url:
            print(f"[WARN] {drama_folder.name} - no cover_url found")
            continue
        
        print(f"[DOWNLOAD] {drama_folder.name}...")
        try:
            response = session.get(cover_url, timeout=30)
            response.raise_for_status()
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            print(f"  OK - {len(response.content)} bytes")
        except Exception as e:
            print(f"  ERROR - {e}")

if __name__ == "__main__":
    download_covers()
