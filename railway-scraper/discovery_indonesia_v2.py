#!/usr/bin/env python3
"""
FlickReels Discovery v2 - Indonesian Dramas ONLY
=================================================
Uses /app/playlet/navigationColumn to get REAL Indonesian content list.
This is the same endpoint the app uses, so we get the same content.

Usage:
    python discovery_indonesia_v2.py              # Discover all Indonesian dramas
    python discovery_indonesia_v2.py --pages=50   # Limit to 50 pages
"""
import os
import sys
import json
import time
import hashlib
import hmac
import random
import string
import argparse
import logging
from typing import Dict, List, Optional

import requests

# ============================================================================
# CONFIGURATION - Exact same as capture from app with Indonesian language
# ============================================================================

FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.getenv("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0"
}

# Request body - EXACTLY from HTTP Toolkit capture with Indonesian language
INDONESIAN_BODY = {
    "main_package_id": 100,
    "googleAdId": "783978b6-0d30-438d-a58d-faf171eed978",
    "device_id": "0d209b4d4009b44c",
    "device_sign": "0ee806655facff8960c6e146fe984fadb52b0cb794cea9a0ed2030d08a179215",
    "apps_flyer_uid": "1769621528308-5741215934785896746",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "language_id": "6",      # INDONESIA - THIS IS THE KEY!
    "countryCode": "ID"      # INDONESIA
}

# Navigation IDs (from capture - different sections of the app)
NAVIGATION_IDS = [
    "30",   # Main/Popular (from capture)
    # Add more if needed
]

# Rate limiting
RATE_LIMIT = 10
MIN_INTERVAL = 1.0 / RATE_LIMIT

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

# ============================================================================
# API SIGNING
# ============================================================================

def generate_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def method_d(body_json):
    if not body_json or body_json == "{}":
        return ""
    data = json.loads(body_json)
    sorted_data = dict(sorted(data.items()))
    parts = []
    for key, value in sorted_data.items():
        if value is not None:
            if isinstance(value, bool):
                value_str = 'true' if value else 'false'
            elif isinstance(value, (list, dict)):
                value_str = json.dumps(value, separators=(',', ':'))
            else:
                value_str = str(value)
            parts.append(f'{key}_{value_str}')
    return '_'.join(parts)

def generate_sign(body, timestamp, nonce):
    body_json = json.dumps(body, separators=(',', ':'))
    str_d = method_d(body_json)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    return hmac.new(
        FLICKREELS_CONFIG["secret_key"].encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

# ============================================================================
# DISCOVERY CLASS
# ============================================================================

class IndonesianDiscoveryV2:
    def __init__(self, output_file="indonesian_dramas.json"):
        self.output_file = output_file
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
        self.dramas = {}  # id -> drama data
        self.last_request = 0
        self.stats = {"pages": 0, "dramas": 0}
        
        # Load existing
        self._load_existing()
    
    def _load_existing(self):
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for drama in data:
                        self.dramas[str(drama.get('id'))] = drama
                logger.info(f"Loaded {len(self.dramas)} existing dramas")
            except Exception as e:
                logger.warning(f"Could not load existing file: {e}")
    
    def _save(self):
        dramas = sorted(self.dramas.values(), key=lambda x: int(x.get('id', 0)))
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(dramas, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(dramas)} dramas to {self.output_file}")
    
    def _rate_limit(self):
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        self.last_request = time.time()
    
    def _request(self, endpoint, extra_body=None):
        try:
            self._rate_limit()
            
            body = {**INDONESIAN_BODY, **(extra_body or {})}
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            sign = generate_sign(body, timestamp, nonce)
            
            headers = {
                "token": FLICKREELS_CONFIG["token"],
                "sign": sign,
                "timestamp": timestamp,
                "nonce": nonce
            }
            
            url = f"{FLICKREELS_CONFIG['base_url']}{endpoint}"
            response = self.session.post(url, json=body, headers=headers, timeout=30)
            
            if response.status_code == 429:
                logger.warning("Rate limited! Waiting 5s...")
                time.sleep(5)
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def get_drama_list(self, navigation_id="30", page=1, page_size=20):
        """Get drama list from navigationColumn endpoint"""
        result = self._request("/app/playlet/navigationColumn", {
            "navigation_id": navigation_id,
            "page": page,
            "page_size": page_size
        })
        
        if not result or result.get("status_code") != 1:
            return []
        
        dramas = []
        data = result.get("data", [])
        
        for section in data:
            for item in section.get("list", []):
                drama = {
                    "id": str(item.get("playlet_id")),
                    "title": item.get("title"),
                    "cover": item.get("cover"),
                    "total_episodes": int(item.get("upload_num", 0)),
                    "description": item.get("introduce", ""),
                    "tags": item.get("playlet_tag_name", [])
                }
                dramas.append(drama)
        
        return dramas
    
    def get_drama_detail(self, drama_id):
        """Get episode details for a drama"""
        result = self._request("/app/playlet/chapterList", {"playlet_id": str(drama_id)})
        
        if not result or result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        chapters = data.get("list", [])
        
        return {
            "title": data.get("title"),
            "cover": data.get("cover"),
            "total_episodes": len(chapters),
            "episodes": [
                {
                    "num": ch.get("chapter_num"),
                    "title": ch.get("chapter_title"),
                    "hls_url": ch.get("hls_url"),
                    "duration": ch.get("duration"),
                    "is_vip": ch.get("is_vip_episode", 0)
                }
                for ch in chapters
            ]
        }
    
    def discover(self, max_pages=100, nav_id="30"):
        """Discover all Indonesian dramas via navigationColumn"""
        logger.info("=" * 60)
        logger.info("INDONESIAN DRAMA DISCOVERY v2")
        logger.info(f"Using endpoint: /app/playlet/navigationColumn")
        logger.info(f"Language: ID (language_id=6, countryCode=ID)")
        logger.info(f"Navigation ID: {nav_id}")
        logger.info(f"Max pages: {max_pages}")
        logger.info("=" * 60)
        
        page = 1
        empty_pages = 0
        
        while page <= max_pages and empty_pages < 3:
            logger.info(f"Fetching page {page}...")
            
            dramas = self.get_drama_list(navigation_id=nav_id, page=page)
            
            if not dramas:
                empty_pages += 1
                logger.info(f"No dramas on page {page} (empty count: {empty_pages})")
            else:
                empty_pages = 0  # Reset
                
                for drama in dramas:
                    drama_id = drama["id"]
                    if drama_id not in self.dramas:
                        self.dramas[drama_id] = drama
                        self.stats["dramas"] += 1
                        logger.info(f"  ✅ [{drama_id}] {drama['title']} ({drama['total_episodes']} eps)")
            
            self.stats["pages"] += 1
            page += 1
            
            # Checkpoint save every 10 pages
            if page % 10 == 0:
                self._save()
        
        # Final save
        self._save()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("DISCOVERY COMPLETE!")
        logger.info(f"  Pages scanned: {self.stats['pages']}")
        logger.info(f"  New dramas found: {self.stats['dramas']}")
        logger.info(f"  Total in database: {len(self.dramas)}")
        logger.info("=" * 60)
        
        return self.dramas
    
    def enrich_with_episodes(self, limit=None):
        """Get episode details for all discovered dramas"""
        count = 0
        total = len(self.dramas) if limit is None else min(limit, len(self.dramas))
        
        logger.info(f"Enriching {total} dramas with episode details...")
        
        for drama_id, drama in list(self.dramas.items()):
            if limit and count >= limit:
                break
            
            # Skip if already has episodes
            if "episodes" in drama and drama["episodes"]:
                continue
            
            detail = self.get_drama_detail(drama_id)
            if detail:
                drama["episodes"] = detail["episodes"]
                drama["total_episodes"] = detail["total_episodes"]
                count += 1
                logger.info(f"  [{count}/{total}] {drama['title']} - {len(detail['episodes'])} episodes")
            
            # Save periodically
            if count % 20 == 0:
                self._save()
        
        self._save()
        logger.info(f"Enriched {count} dramas with episode data")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Discover Indonesian dramas from FlickReels')
    parser.add_argument('--pages', type=int, default=100, help='Max pages to scan')
    parser.add_argument('--nav-id', type=str, default='30', help='Navigation ID')
    parser.add_argument('--output', type=str, default='indonesian_dramas.json', help='Output file')
    parser.add_argument('--enrich', action='store_true', help='Also fetch episode details')
    parser.add_argument('--enrich-limit', type=int, default=None, help='Limit episodes to fetch')
    args = parser.parse_args()
    
    discovery = IndonesianDiscoveryV2(output_file=args.output)
    discovery.discover(max_pages=args.pages, nav_id=args.nav_id)
    
    if args.enrich:
        discovery.enrich_with_episodes(limit=args.enrich_limit)

if __name__ == "__main__":
    main()
