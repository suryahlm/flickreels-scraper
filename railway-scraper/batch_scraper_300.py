#!/usr/bin/env python3
"""
FlickReels Batch Scraper - 300 Indonesian Dramas
=================================================
Scrapes Indonesian dramas to R2 with same structure as existing 42 dramas.

Usage:
    railway run python batch_scraper_300.py
    railway run python batch_scraper_300.py --start=0 --count=50
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urljoin

import requests
import boto3
from botocore.config import Config

# ============================================================================
# CONFIGURATION
# ============================================================================

R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "asiandrama-cdn"),
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com"
}

FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.getenv("FLICKREELS_TOKEN"),
    "version": "2.2.3.0"
}

# INDONESIAN ONLY - language_id = 6
DEFAULT_BODY = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "54635c70fbd4b9ece7bcac55af30c6a48a63a8fedcf7f61c4a54cd8604ab4851",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID",
    "language_id": "6"  # INDONESIAN ONLY
}

CONCURRENCY = {
    "max_dramas": 1,        # One drama at a time for stability
    "max_episodes": 12,      # 12 parallel episodes per drama
    "max_segments": 4,       # 4 parallel segments per episode
    "rate_limit": 12,        # 12 requests per second
    "retry_attempts": 5,
    "timeout": 60,
}

# Logging with utf-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('batch_scraper.log', encoding='utf-8')
    ]
)
# Force UTF-8 for stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    def __init__(self, max_per_second=12):
        self.min_interval = 1.0 / max_per_second
        self.last_call = 0
        self.lock = Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_call = time.time()

rate_limiter = RateLimiter(CONCURRENCY["rate_limit"])

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
# API CLIENT
# ============================================================================

class FlickReelsAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
    
    def _request(self, endpoint, extra_body=None, retries=5):
        for attempt in range(retries):
            try:
                rate_limiter.acquire()
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
                    wait = (2 ** attempt) * 3
                    logger.warning(f"Rate limited! Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Request failed after {retries} attempts: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None
    
    def get_indonesian_dramas(self, page=1, page_size=50):
        """Get list of Indonesian dramas from latestPlay"""
        result = self._request("/app/playlet/latestPlay", {
            "page": str(page),
            "page_size": str(page_size)
        })
        if not result or result.get("status_code") != 1:
            return []
        return result.get("data", {}).get("list", [])
    
    def get_hot_dramas(self):
        """Get hot dramas from hotRank"""
        result = self._request("/app/playlet/hotRank", {})
        if not result or result.get("status_code") != 1:
            return []
        # hotRank returns list of categories with dramas
        dramas = []
        for category in result.get("data", []):
            for drama in category.get("data", []):
                dramas.append(drama)
        return dramas
    
    def get_navigation_dramas(self):
        """Get dramas from navigation endpoint"""
        result = self._request("/app/playlet/navigation", {})
        if not result or result.get("status_code") != 1:
            return []
        dramas = []
        data = result.get("data", [])
        # Handle both list and dict formats
        if isinstance(data, list):
            for nav in data:
                for item in nav.get("list", []):
                    dramas.append(item)
        elif isinstance(data, dict):
            for nav in data.get("list", []):
                for item in nav.get("list", []):
                    dramas.append(item)
        return dramas
    
    def get_drama_detail(self, drama_id):
        """Get drama details with episodes and HLS URLs"""
        result = self._request("/app/playlet/chapterList", {"playlet_id": str(drama_id)})
        if not result or result.get("status_code") != 1:
            return None
        data = result.get("data", {})
        return {
            "title": data.get("title", f"Drama {drama_id}"),
            "cover_url": data.get("cover"),
            "chapter_list": data.get("list", []),
            "language_name": data.get("language_name", ""),
        }

# ============================================================================
# R2 UPLOADER
# ============================================================================

class R2Uploader:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG["endpoint_url"],
            aws_access_key_id=R2_CONFIG["access_key_id"],
            aws_secret_access_key=R2_CONFIG["secret_access_key"],
            config=Config(signature_version='s3v4')
        )
        self.bucket = R2_CONFIG["bucket_name"]
    
    def upload_stream(self, url, r2_key, content_type=None, retries=5):
        for attempt in range(retries):
            try:
                rate_limiter.acquire()
                response = requests.get(url, stream=True, timeout=CONCURRENCY["timeout"])
                response.raise_for_status()
                
                self.client.upload_fileobj(
                    response.raw,
                    self.bucket,
                    r2_key,
                    ExtraArgs={'ContentType': content_type} if content_type else {}
                )
                return True
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Upload failed {r2_key}: {e}")
                    return False
                time.sleep(2 ** attempt)
        return False
    
    def upload_bytes(self, content, r2_key, content_type=None):
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=r2_key,
                Body=content,
                ContentType=content_type or 'application/octet-stream'
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed {r2_key}: {e}")
            return False
    
    def upload_json(self, data, r2_key):
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        return self.upload_bytes(json_bytes, r2_key, 'application/json')
    
    def key_exists(self, r2_key):
        try:
            self.client.head_object(Bucket=self.bucket, Key=r2_key)
            return True
        except:
            return False

# ============================================================================
# BATCH SCRAPER
# ============================================================================

class BatchScraper:
    """Batch scraper for 300 Indonesian dramas"""
    
    def __init__(self):
        self.api = FlickReelsAPI()
        self.uploader = R2Uploader()
        self.stats = {
            "dramas_done": 0,
            "dramas_failed": 0,
            "dramas_skipped": 0,
            "episodes_done": 0,
            "episodes_failed": 0,
            "segments_uploaded": 0,
        }
        self.lock = Lock()
    
    def get_existing_drama_ids(self):
        """Get list of drama IDs already in R2"""
        existing = set()
        try:
            paginator = self.uploader.client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.uploader.bucket, Prefix='flickreels/', Delimiter='/'):
                for prefix in page.get('CommonPrefixes', []):
                    folder = prefix['Prefix']
                    if '(' in folder and ')' in folder:
                        drama_id = folder.split('(')[-1].replace(')', '').replace('/', '')
                        existing.add(drama_id)
        except Exception as e:
            logger.warning(f"Could not get existing dramas: {e}")
        return existing
    
    def parse_m3u8(self, content, base_url):
        segments = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.endswith('.ts') or '.ts?' in line:
                if not line.startswith('http'):
                    line = urljoin(base_url, line)
                segments.append(line)
        return segments
    
    def rewrite_m3u8(self, content, episode_prefix):
        lines = content.strip().split('\n')
        new_lines = []
        idx = 0
        for line in lines:
            line = line.strip()
            if line.endswith('.ts') or '.ts?' in line:
                new_lines.append(f"{episode_prefix}_{idx:04d}.ts")
                idx += 1
            else:
                new_lines.append(line)
        return '\n'.join(new_lines)
    
    def scrape_episode(self, drama_id, episode_num, hls_url, r2_path):
        """Scrape single episode"""
        try:
            if not hls_url:
                return False
            
            # Download manifest
            rate_limiter.acquire()
            response = requests.get(hls_url, timeout=30)
            response.raise_for_status()
            m3u8_content = response.text
            
            # Parse segments
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            segments = self.parse_m3u8(m3u8_content, base_url)
            
            if not segments:
                return False
            
            episode_prefix = f"ep_{episode_num:03d}"
            
            # Upload segments with parallel workers
            success_count = 0
            with ThreadPoolExecutor(max_workers=CONCURRENCY["max_segments"]) as executor:
                futures = []
                for i, segment_url in enumerate(segments):
                    r2_key = f"{r2_path}/{episode_prefix}_{i:04d}.ts"
                    future = executor.submit(
                        self.uploader.upload_stream,
                        segment_url, r2_key, "video/mp2t"
                    )
                    futures.append(future)
                
                for f in as_completed(futures):
                    if f.result():
                        success_count += 1
            
            if success_count == 0:
                return False
            
            # Upload rewritten m3u8
            rewritten = self.rewrite_m3u8(m3u8_content, episode_prefix)
            m3u8_key = f"{r2_path}/{episode_prefix}.m3u8"
            self.uploader.upload_bytes(rewritten.encode(), m3u8_key, 'application/vnd.apple.mpegurl')
            
            with self.lock:
                self.stats["episodes_done"] += 1
                self.stats["segments_uploaded"] += success_count
            
            return True
            
        except Exception as e:
            logger.error(f"Episode {episode_num} error: {e}")
            with self.lock:
                self.stats["episodes_failed"] += 1
            return False
    
    def scrape_drama(self, drama_id, title=None):
        """Scrape single drama with all episodes"""
        try:
            logger.info(f"{'='*60}")
            logger.info(f"SCRAPING: {title or drama_id} (ID: {drama_id})")
            logger.info(f"{'='*60}")
            
            # Get drama details
            detail = self.api.get_drama_detail(drama_id)
            if not detail:
                logger.error(f"Failed to get drama details for {drama_id}")
                with self.lock:
                    self.stats["dramas_failed"] += 1
                return False
            
            drama_title = detail.get("title", f"Drama {drama_id}")
            cover_url = detail.get("cover_url")
            chapters = detail.get("chapter_list", [])
            
            logger.info(f"Title: {drama_title}")
            logger.info(f"Episodes: {len(chapters)}")
            
            # Create R2 path: {Title} ({ID})
            safe_title = "".join(c for c in drama_title if c.isalnum() or c in ' _-').strip()
            r2_path = f"flickreels/{safe_title} ({drama_id})"
            
            # Download and upload cover
            if cover_url:
                try:
                    response = requests.get(cover_url, timeout=30)
                    if len(response.content) > 1000:
                        self.uploader.upload_bytes(
                            response.content, 
                            f"{r2_path}/cover.jpg", 
                            'image/jpeg'
                        )
                        logger.info(f"✅ Cover uploaded")
                except Exception as e:
                    logger.warning(f"Cover failed: {e}")
            
            # Upload metadata
            metadata = {
                "id": drama_id,
                "title": drama_title,
                "cover_url": cover_url,
                "total_episodes": len(chapters),
                "language": detail.get("language_name", "Indonesian"),
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.uploader.upload_json(metadata, f"{r2_path}/metadata.json")
            
            # Scrape episodes with 12 parallel workers
            logger.info(f"Scraping {len(chapters)} episodes with {CONCURRENCY['max_episodes']} workers...")
            
            with ThreadPoolExecutor(max_workers=CONCURRENCY["max_episodes"]) as executor:
                futures = []
                for i, chapter in enumerate(chapters, 1):
                    hls_url = chapter.get("hls_url", "")
                    if hls_url:
                        future = executor.submit(
                            self.scrape_episode,
                            drama_id, i, hls_url, r2_path
                        )
                        futures.append((i, future))
                
                # Wait and log progress
                completed = 0
                for ep_num, future in futures:
                    result = future.result()
                    completed += 1
                    if result:
                        logger.info(f"  ✅ Episode {ep_num} done")
                    else:
                        logger.error(f"  ❌ Episode {ep_num} failed")
            
            # Upload completion marker
            complete_data = {
                "id": drama_id,
                "title": drama_title,
                "total_episodes": len(chapters),
                "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.uploader.upload_json(complete_data, f"{r2_path}/complete.json")
            
            with self.lock:
                self.stats["dramas_done"] += 1
            
            logger.info(f"✅ DRAMA COMPLETE: {drama_title}")
            return True
            
        except Exception as e:
            logger.error(f"Drama {drama_id} failed: {e}")
            with self.lock:
                self.stats["dramas_failed"] += 1
            return False
    
    def collect_drama_ids(self, existing_ids, max_count=300):
        """Collect drama IDs from all sources"""
        collected = {}  # id -> title
        
        # 1. From latestPlay (multiple pages)
        logger.info("Fetching from latestPlay...")
        for page in range(1, 20):
            dramas = self.api.get_indonesian_dramas(page=page, page_size=50)
            if not dramas:
                break
            for d in dramas:
                drama_id = str(d.get("playlet_id"))
                if drama_id not in existing_ids and drama_id not in collected:
                    collected[drama_id] = d.get("title", "")
            if len(collected) >= max_count:
                break
            time.sleep(0.5)
        
        logger.info(f"  Found {len(collected)} from latestPlay")
        
        # 2. From hotRank
        logger.info("Fetching from hotRank...")
        for d in self.api.get_hot_dramas():
            drama_id = str(d.get("playlet_id"))
            if drama_id not in existing_ids and drama_id not in collected:
                collected[drama_id] = d.get("title", "")
        logger.info(f"  Total now: {len(collected)}")
        
        # 3. From navigation
        logger.info("Fetching from navigation...")
        for d in self.api.get_navigation_dramas():
            drama_id = str(d.get("playlet_id"))
            if drama_id not in existing_ids and drama_id not in collected:
                collected[drama_id] = d.get("title", "")
        logger.info(f"  Total now: {len(collected)}")
        
        # 4. Scan ID ranges if still need more (most dramas are 1000-6000)
        if len(collected) < max_count:
            logger.info("Scanning ID ranges for Indonesian dramas...")
            for scan_id in range(5500, 1000, -1):  # Start from recent, go backwards
                if len(collected) >= max_count:
                    break
                scan_id = str(scan_id)
                if scan_id in existing_ids or scan_id in collected:
                    continue
                
                # Get drama details and check language
                detail = self.api.get_drama_detail(scan_id)
                if detail:
                    title = detail.get("title", "")
                    language = detail.get("language_name", "").lower()
                    chapters = detail.get("chapter_list", [])
                    
                    # Only include INDONESIAN dramas
                    if title and len(chapters) > 0 and "indonesian" in language:
                        collected[scan_id] = title
                        logger.info(f"  Found ID {scan_id}: {title} ({len(chapters)} eps)")
                        
                        if len(collected) >= max_count:
                            break
        
        return collected
    
    def run(self, start_page=1, target_total=300):
        """Run batch scraping until reaching target TOTAL dramas in R2"""
        logger.info(f"{'='*60}")
        logger.info(f"BATCH SCRAPER - TARGET: {target_total} TOTAL DRAMAS IN R2")
        logger.info(f"{'='*60}")
        
        if not FLICKREELS_CONFIG["token"]:
            logger.error("FLICKREELS_TOKEN not set!")
            return
        
        # Get existing dramas
        existing_ids = self.get_existing_drama_ids()
        current_total = len(existing_ids)
        logger.info(f"Current dramas in R2: {current_total}")
        
        if current_total >= target_total:
            logger.info(f"Target already reached! ({current_total}/{target_total})")
            return
        
        needed = target_total - current_total
        logger.info(f"Need to scrape: {needed} new dramas")
        
        # Collect drama IDs from all sources
        collected = self.collect_drama_ids(existing_ids, needed + 50)  # Get extra for failures
        drama_queue = list(collected.items())  # [(id, title), ...]
        logger.info(f"Found {len(drama_queue)} candidate dramas")
        
        # Track IDs we've already attempted
        attempted_ids = set()
        scraped_successfully = 0
        queue_index = 0
        
        # Keep scraping until we reach target
        while scraped_successfully < needed:
            # Get next drama from queue
            if queue_index < len(drama_queue):
                drama_id, title = drama_queue[queue_index]
                queue_index += 1
            else:
                # Queue exhausted, try scanning more IDs for Indonesian dramas
                logger.info("Queue exhausted, scanning for more Indonesian dramas...")
                for scan_id in range(6000, 500, -1):
                    scan_id = str(scan_id)
                    if scan_id in existing_ids or scan_id in attempted_ids:
                        continue
                    detail = self.api.get_drama_detail(scan_id)
                    if detail:
                        title = detail.get("title", "")
                        language = detail.get("language_name", "").lower()
                        chapters = detail.get("chapter_list", [])
                        # Only INDONESIAN dramas
                        if title and len(chapters) > 0 and "indonesian" in language:
                            drama_id = scan_id
                            logger.info(f"Found Indonesian via scan: {drama_id} - {title}")
                            break
                else:
                    logger.error("No more Indonesian dramas available to scan!")
                    break
            
            # Skip if already attempted
            if drama_id in attempted_ids:
                continue
            attempted_ids.add(drama_id)
            
            # Attempt to scrape
            progress = f"[{scraped_successfully + 1 + current_total}/{target_total}]"
            logger.info(f"\n{progress} Scraping: {title} (ID: {drama_id})")
            
            success = self.scrape_drama(drama_id, title)
            
            if success:
                scraped_successfully += 1
                logger.info(f"PROGRESS: {scraped_successfully}/{needed} new dramas done, "
                           f"Total in R2: {current_total + scraped_successfully}/{target_total}")
            else:
                logger.warning(f"Failed {drama_id}, will find replacement...")
        
        # Final stats
        final_total = current_total + scraped_successfully
        logger.info(f"\n{'='*60}")
        logger.info("BATCH SCRAPING COMPLETE!")
        logger.info(f"  Started with: {current_total} dramas")
        logger.info(f"  Successfully scraped: {self.stats['dramas_done']}")
        logger.info(f"  Failed (replaced): {self.stats['dramas_failed']}")
        logger.info(f"  Final total in R2: {final_total}/{target_total}")
        logger.info(f"  Episodes done: {self.stats['episodes_done']}")
        logger.info(f"  Segments uploaded: {self.stats['segments_uploaded']}")
        logger.info(f"{'='*60}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Batch Scraper - Target 300 TOTAL Indonesian Dramas in R2')
    parser.add_argument('--target', type=int, default=300, help='Target TOTAL dramas in R2 (existing + new)')
    args = parser.parse_args()
    
    scraper = BatchScraper()
    scraper.run(target_total=args.target)

if __name__ == "__main__":
    main()
