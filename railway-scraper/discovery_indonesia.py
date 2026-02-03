#!/usr/bin/env python3
"""
FlickReels Discovery - Indonesian Dramas
=========================================
Scans ID range to discover all Indonesian dramas.
Uses /app/playlet/chapterList endpoint with language_id=6 and countryCode=ID.

Usage:
    python discovery_indonesia.py                    # Full scan 1-6000
    python discovery_indonesia.py --range=1-500      # Partial scan
    python discovery_indonesia.py --dry-run          # Test without saving
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
# CONFIGURATION
# ============================================================================

FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.getenv("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0"
}

# Request body dengan parameter lengkap dari HTTP Toolkit capture
DEFAULT_BODY = {
    "main_package_id": 100,
    "googleAdId": "783978b6-0d30-438d-a58d-faf171eed978",
    "device_id": "0d209b4d4009b44c",
    "device_sign": "5af6b3970595e1df2a4be3df91ec58cbab23f04e847db0b89c33eb7eadd51f79",
    "apps_flyer_uid": "1769621528308-5741215934785896746",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "language_id": "6",      # INDONESIA
    "countryCode": "ID"      # INDONESIA - parameter baru dari capture!
}

# Rate limiting
RATE_LIMIT = 12  # requests per second
MIN_INTERVAL = 1.0 / RATE_LIMIT

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

# ============================================================================
# API SIGNING (sama dengan batch_scraper_300.py)
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

class IndonesiaDiscovery:
    def __init__(self, output_file="discovered_indonesia.json"):
        self.output_file = output_file
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
        self.discovered = {}  # id -> drama data
        self.last_request = 0
        self.stats = {
            "scanned": 0,
            "found": 0,
            "errors": 0,
            "skipped": 0
        }
        
        # Load existing data if available
        self._load_existing()
    
    def _load_existing(self):
        """Load existing discovered dramas"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for drama in data:
                        self.discovered[str(drama.get('id'))] = drama
                logger.info(f"Loaded {len(self.discovered)} existing dramas from {self.output_file}")
            except Exception as e:
                logger.warning(f"Could not load existing file: {e}")
    
    def _save(self):
        """Save discovered dramas to JSON"""
        dramas = sorted(self.discovered.values(), key=lambda x: int(x.get('id', 0)))
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(dramas, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(dramas)} dramas to {self.output_file}")
    
    def _rate_limit(self):
        """Simple rate limiting"""
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        self.last_request = time.time()
    
    def _request(self, endpoint, extra_body=None):
        """Make API request with signing"""
        try:
            self._rate_limit()
            
            body = {**DEFAULT_BODY, **(extra_body or {})}
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
            logger.debug(f"Request error: {e}")
            return None
    
    def is_indonesian_title(self, title):
        """
        Check if title appears to be Indonesian
        Based on common Indonesian words and patterns
        """
        title_lower = title.lower()
        
        # EXCLUDE: Spanish/Portuguese patterns
        spanish_patterns = [
            "ñ", "á", "é", "í", "ó", "ú",  # Spanish accents
            " de ", " la ", " el ", " los ", " las ",  # Spanish articles
            " del ", " por ", " que ", " una ", " uno ",
            "venganza", "trampa", "belleza", "cuñada",
            "perdona", "olvida", "atrapados"
        ]
        for pattern in spanish_patterns:
            if pattern in title_lower:
                return False
        
        # EXCLUDE: Chinese patterns (characters)
        if any('\u4e00' <= c <= '\u9fff' for c in title):
            return False
        
        # INCLUDE: Indonesian keywords (strong indicators)
        indonesian_keywords = [
            "cinta", "kasih", "sayang", "rindu",  # Love
            "istri", "suami", "ibu", "ayah", "anak", "adik", "kakak",  # Family
            "ceo", "bos", "boss", "presdir",  # Office drama
            "rahasia", "dendam", "balasan",  # Drama
            "tidak", "bukan", "jangan", "hanya",  # Common words
            "aku", "kamu", "dia", "kami", "mereka",  # Pronouns
            "seorang", "seseorang", "sebuah",  # Articles
            "permaisuri", "raja", "ratu", "pangeran", "putri",  # Royalty
            "menikah", "pernikahan", "nikah",  # Marriage
            "hamil", "kehamilan",  # Pregnancy
            "pengemis", "miskin", "kaya",  # Status
            "-ku", "-mu", "-nya",  # Suffixes
            "memanjakan", "mengandung", "mendapat"  # Verbs
        ]
        for keyword in indonesian_keywords:
            if keyword in title_lower:
                return True
        
        # INCLUDE: Title starts with common Indonesian patterns
        indonesian_starts = [
            "aku ", "kau ", "dia ", "sang ", "si ", 
            "kisah ", "cinta ", "rahasia ", "dendam "
        ]
        for start in indonesian_starts:
            if title_lower.startswith(start):
                return True
        
        # If no strong Indonesian indicator and no Spanish, 
        # check if it looks like English (which might be translated)
        # For now, reject if unclear
        return False
    
    def probe_drama(self, drama_id):
        """
        Probe a single drama ID to check if it's Indonesian
        Returns drama data if Indonesian, None otherwise
        """
        result = self._request("/app/playlet/chapterList", {"playlet_id": str(drama_id)})
        
        if not result or result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        title = data.get("title", "")
        chapters = data.get("list", [])
        cover = data.get("cover", "")
        
        # Must have title and episodes
        if not title or not chapters:
            return None
        
        # Check if title is Indonesian
        if not self.is_indonesian_title(title):
            logger.debug(f"  [{drama_id}] Rejected (not Indonesian): {title}")
            return None
        
        # Return drama info
        return {
            "id": str(drama_id),
            "title": title,
            "cover": cover,
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

    
    def discover(self, start_id=1, end_id=6000, dry_run=False):
        """
        Scan ID range to discover Indonesian dramas
        """
        logger.info(f"=" * 60)
        logger.info(f"DISCOVERY: Scanning ID {start_id} to {end_id}")
        logger.info(f"Rate limit: {RATE_LIMIT} req/sec")
        logger.info(f"Output: {self.output_file}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"=" * 60)
        
        checkpoint_interval = 50  # Save every 50 IDs checked
        
        for drama_id in range(start_id, end_id + 1):
            # Skip if already discovered
            if str(drama_id) in self.discovered:
                self.stats["skipped"] += 1
                continue
            
            self.stats["scanned"] += 1
            
            # Probe this ID
            drama = self.probe_drama(drama_id)
            
            if drama:
                self.discovered[str(drama_id)] = drama
                self.stats["found"] += 1
                logger.info(f"✅ [{drama_id}] {drama['title']} ({drama['total_episodes']} eps)")
            else:
                logger.debug(f"   [{drama_id}] Not found or not Indonesian")
            
            # Checkpoint save
            if not dry_run and self.stats["scanned"] % checkpoint_interval == 0:
                self._save()
                logger.info(f"--- Checkpoint: {self.stats['scanned']} scanned, {self.stats['found']} found ---")
            
            # Progress every 100
            if self.stats["scanned"] % 100 == 0:
                logger.info(f"Progress: Scanned {self.stats['scanned']}, Found {self.stats['found']}, Skipped {self.stats['skipped']}")
        
        # Final save
        if not dry_run:
            self._save()
        
        # Print summary
        logger.info(f"\n" + "=" * 60)
        logger.info(f"DISCOVERY COMPLETE!")
        logger.info(f"  Range: {start_id} - {end_id}")
        logger.info(f"  Scanned: {self.stats['scanned']}")
        logger.info(f"  Found: {self.stats['found']}")
        logger.info(f"  Skipped (existing): {self.stats['skipped']}")
        logger.info(f"  Total in database: {len(self.discovered)}")
        logger.info(f"=" * 60)
        
        return self.discovered

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Discover Indonesian dramas via ID range scanning')
    parser.add_argument('--range', type=str, default='1-6000', 
                       help='ID range to scan (e.g., 1-6000)')
    parser.add_argument('--output', type=str, default='discovered_indonesia.json',
                       help='Output JSON file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test without saving')
    args = parser.parse_args()
    
    # Parse range
    try:
        start, end = map(int, args.range.split('-'))
    except:
        logger.error(f"Invalid range format: {args.range}. Use format: START-END")
        return
    
    # Run discovery
    discovery = IndonesiaDiscovery(output_file=args.output)
    discovery.discover(start_id=start, end_id=end, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
