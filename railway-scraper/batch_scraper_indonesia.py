#!/usr/bin/env python3
"""
FlickReels Indonesian Batch Scraper - Railway Edition
======================================================
PRODUCTION-READY for Railway deployment!

1. Uses /navigationColumn to discover REAL Indonesian dramas
2. Downloads with 12 parallel episodes (nested structure)
3. Uploads to Supabase database

Usage:
    python batch_scraper_indonesia.py              # Scrape all
    python batch_scraper_indonesia.py --limit=5    # Test with 5 dramas
    python batch_scraper_indonesia.py --fresh      # Clear progress and restart
"""
import os
import sys
import re
import json
import time
import hashlib
import hmac
import random
import string
import logging
import argparse
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import requests

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("ERROR: boto3 required. pip install boto3")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "asiandrama-cdn"),
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com",
    "public_url": "https://cdn.asianreels.me"
}

FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.getenv("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0"
}

# SUPABASE CONFIG - MUST MATCH THE APP!
SUPABASE_CONFIG = {
    "url": os.getenv("SUPABASE_URL", "https://bmryonqbddbkjbtquhgu.supabase.co"),
    "key": os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ")
}

# INDONESIAN ONLY! Same as HTTP Toolkit capture
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
    "language_id": "6",      # INDONESIA
    "countryCode": "ID"      # INDONESIA
}

CONCURRENT_CONFIG = {
    "max_concurrent_episodes": 12,
    "max_concurrent_segments": 4,
    "max_requests_per_second": 15,
    "retry_attempts": 5,
    "request_timeout": 60,
}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITER & API SIGNING
# ============================================================================

class RateLimiter:
    def __init__(self, max_per_second=15):
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

rate_limiter = RateLimiter(max_per_second=CONCURRENT_CONFIG["max_requests_per_second"])

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

class IndonesianAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
    
    def _request(self, endpoint, extra_body=None, retries=3):
        for attempt in range(retries):
            try:
                rate_limiter.acquire()
                
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
                    wait = (2 ** attempt) * 2
                    logger.warning(f"Rate limited! Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"API error: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None
    
    def get_indonesian_dramas(self, page=1, page_size=20, nav_id="30"):
        """Get Indonesian dramas from navigationColumn"""
        result = self._request("/app/playlet/navigationColumn", {
            "navigation_id": nav_id,
            "page": page,
            "page_size": page_size
        })
        
        if not result or result.get("status_code") != 1:
            return []
        
        dramas = []
        for section in result.get("data", []):
            for item in section.get("list", []):
                dramas.append({
                    "id": str(item.get("playlet_id")),
                    "title": item.get("title"),
                    "cover": item.get("cover"),
                    "total_episodes": int(item.get("upload_num") or 0),
                    "description": item.get("introduce", ""),
                    "tags": item.get("playlet_tag_name", [])
                })
        
        return dramas
    
    def get_drama_detail(self, drama_id):
        """Get drama detail with episodes"""
        result = self._request("/app/playlet/chapterList", {"playlet_id": str(drama_id)})
        
        if not result or result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        return {
            "title": data.get("title"),
            "cover": data.get("cover"),
            "episodes": [
                {
                    "chapter_id": ep.get("chapter_id"),
                    "num": ep.get("sort", i+1),
                    "title": ep.get("chapter_title")
                }
                for i, ep in enumerate(data.get("list", []))
            ]
        }
    
    def get_stream_url(self, drama_id, chapter_id):
        """Get HLS URL for episode"""
        result = self._request("/app/playlet/play", {
            "playlet_id": str(drama_id),
            "chapter_id": str(chapter_id)
        })
        
        if not result or result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        return data.get("hls_url") or data.get("hls")

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
    
    def upload_stream(self, url, r2_key, content_type=None, retries=3):
        for attempt in range(retries):
            try:
                rate_limiter.acquire()
                response = requests.get(url, stream=True, timeout=60)
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
                    logger.error(f"Upload failed: {r2_key} - {e}")
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
            logger.error(f"Upload bytes failed: {r2_key} - {e}")
            return False
    
    def upload_json(self, data, r2_key):
        content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        return self.upload_bytes(content, r2_key, 'application/json')

# ============================================================================
# SUPABASE CLIENT
# ============================================================================

class SupabaseClient:
    def __init__(self):
        self.base_url = SUPABASE_CONFIG["url"]
        self.headers = {
            "apikey": SUPABASE_CONFIG["key"],
            "Authorization": f"Bearer {SUPABASE_CONFIG['key']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
    
    def insert_drama(self, drama_data):
        """Insert or update drama in database (upsert by flickreels_id)"""
        try:
            fid = drama_data.get('flickreels_id')
            
            # Check if exists
            check_resp = requests.get(
                f"{self.base_url}/rest/v1/dramas?flickreels_id=eq.{fid}&select=id",
                headers={"apikey": SUPABASE_CONFIG["key"]}
            )
            existing = check_resp.json() if check_resp.status_code == 200 else []
            
            if existing:
                # UPDATE existing
                response = requests.patch(
                    f"{self.base_url}/rest/v1/dramas?flickreels_id=eq.{fid}",
                    headers=self.headers,
                    json=drama_data
                )
                logger.info(f"Updated drama {fid} in Supabase")
            else:
                # INSERT new
                response = requests.post(
                    f"{self.base_url}/rest/v1/dramas",
                    headers=self.headers,
                    json=drama_data
                )
                logger.info(f"Inserted drama {fid} in Supabase")
            
            return response.status_code in [200, 201, 204]
        except Exception as e:
            logger.error(f"Supabase error: {e}")
            return False

# ============================================================================
# CONCURRENT SCRAPER
# ============================================================================

class IndonesianBatchScraper:
    def __init__(self):
        self.api = IndonesianAPI()
        self.uploader = R2Uploader()
        self.supabase = SupabaseClient()
        self.stats = {
            "dramas_processed": 0,
            "episodes_uploaded": 0,
            "start_time": time.time()
        }
        self.stats_lock = Lock()
        self.scraped_ids = set()
        self._load_progress()
    
    def _load_progress(self):
        """Load already scraped IDs from Supabase (persistent across deploys)"""
        try:
            resp = requests.get(
                f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
                headers={"apikey": SUPABASE_CONFIG["key"]}
            )
            if resp.status_code == 200:
                for d in resp.json():
                    if d.get('flickreels_id'):
                        self.scraped_ids.add(str(d['flickreels_id']))
                logger.info(f"Loaded {len(self.scraped_ids)} already scraped IDs from Supabase")
            else:
                logger.warning(f"Could not load progress from Supabase: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error loading progress: {e}")
    
    def _save_progress(self, drama_id):
        self.scraped_ids.add(drama_id)
        with open("scraped_ids.txt", "a") as f:
            f.write(f"{drama_id}\n")
    
    def _clear_progress(self):
        if os.path.exists("scraped_ids.txt"):
            os.remove("scraped_ids.txt")
        self.scraped_ids = set()
        logger.info("Cleared progress")
    
    def parse_m3u8(self, content, base_url):
        segments = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line.startswith('#') and ('.ts' in line):
                if not line.startswith('http'):
                    from urllib.parse import urljoin
                    line = urljoin(base_url, line)
                segments.append(line)
        return segments
    
    def scrape_episode(self, drama_id, episode_num, chapter_id, r2_base):
        """Scrape single episode with NESTED structure: ep_XXX/index.m3u8"""
        try:
            hls_url = self.api.get_stream_url(drama_id, chapter_id)
            if not hls_url:
                logger.error(f"  [EP {episode_num}] No HLS URL")
                return False
            
            # Download manifest
            rate_limiter.acquire()
            response = requests.get(hls_url, timeout=30)
            m3u8_content = response.text
            
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            segments = self.parse_m3u8(m3u8_content, base_url)
            
            if not segments:
                logger.warning(f"  [EP {episode_num}] No segments")
                return False
            
            # NESTED STRUCTURE: ep_XXX/segment_NNNN.ts
            ep_folder = f"ep_{episode_num:03d}"
            r2_ep_dir = f"{r2_base}/{ep_folder}"
            
            # Upload segments
            with ThreadPoolExecutor(max_workers=CONCURRENT_CONFIG["max_concurrent_segments"]) as ex:
                futures = []
                for i, seg_url in enumerate(segments):
                    r2_key = f"{r2_ep_dir}/segment_{i:04d}.ts"
                    futures.append(ex.submit(self.uploader.upload_stream, seg_url, r2_key, "video/mp2t"))
                
                success_count = sum(1 for f in futures if f.result())
            
            if success_count < len(segments):
                logger.error(f"  [EP {episode_num}] Only {success_count}/{len(segments)} segments")
                return False
            
            # Rewrite manifest with RELATIVE paths (just segment_NNNN.ts)
            new_lines = []
            seg_idx = 0
            for line in m3u8_content.strip().split('\n'):
                if not line.startswith('#') and ('.ts' in line):
                    new_lines.append(f"segment_{seg_idx:04d}.ts")
                    seg_idx += 1
                else:
                    new_lines.append(line)
            
            new_m3u8 = '\n'.join(new_lines)
            
            # Upload manifest as index.m3u8 in episode folder
            self.uploader.upload_bytes(
                new_m3u8.encode('utf-8'),
                f"{r2_ep_dir}/index.m3u8",
                "application/vnd.apple.mpegurl"
            )
            
            with self.stats_lock:
                self.stats["episodes_uploaded"] += 1
            
            logger.info(f"  [EP {episode_num}] ✅ {len(segments)} segments")
            return True
            
        except Exception as e:
            logger.error(f"  [EP {episode_num}] Error: {e}")
            return False
    
    def scrape_drama(self, drama):
        """Scrape single drama with 12 concurrent episodes"""
        drama_id = drama["id"]
        title = drama["title"]
        
        if drama_id in self.scraped_ids:
            logger.info(f"Skipping {title} (already scraped)")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SCRAPING: {title} (ID: {drama_id})")
        logger.info(f"{'='*60}")
        
        # Get episode details
        detail = self.api.get_drama_detail(drama_id)
        if not detail or not detail.get("episodes"):
            logger.error(f"No episodes found for {title}")
            return
        
        episodes = detail["episodes"]
        logger.info(f"Episodes: {len(episodes)}")
        
        # R2 path with title
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        r2_base = f"flickreels/{clean_title} ({drama_id})"
        
        # Scrape episodes with 12 parallel workers
        with ThreadPoolExecutor(max_workers=CONCURRENT_CONFIG["max_concurrent_episodes"]) as ex:
            futures = []
            for ep in episodes:
                ep_num = ep["num"]
                chapter_id = ep["chapter_id"]
                futures.append((ep_num, ex.submit(
                    self.scrape_episode, drama_id, ep_num, chapter_id, r2_base
                )))
            
            success = sum(1 for num, f in futures if f.result())
        
        logger.info(f"Uploaded {success}/{len(episodes)} episodes")
        
        # Download and upload cover image
        cover_url = drama.get("cover") or detail.get("cover", "")
        r2_cover_path = ""
        if cover_url:
            logger.info(f"Downloading cover image...")
            try:
                cover_response = requests.get(cover_url, timeout=30)
                if cover_response.status_code == 200:
                    # Determine extension
                    ext = "jpg"
                    if "png" in cover_url.lower():
                        ext = "png"
                    elif "webp" in cover_url.lower():
                        ext = "webp"
                    
                    r2_cover_key = f"{r2_base}/cover.{ext}"
                    if self.uploader.upload_bytes(cover_response.content, r2_cover_key, f"image/{ext}"):
                        r2_cover_path = r2_cover_key
                        logger.info(f"✅ Cover uploaded: {r2_cover_key}")
                    else:
                        logger.warning(f"Failed to upload cover")
                else:
                    logger.warning(f"Cover download failed: {cover_response.status_code}")
            except Exception as e:
                logger.warning(f"Cover error: {e}")
        
        # Upload metadata
        metadata = {
            "id": drama_id,
            "title": title,
            "cover": cover_url,
            "cover_r2": r2_cover_path,
            "description": drama.get("description", ""),
            "total_episodes": len(episodes),
            "genres": drama.get("tags", []),
            "scraped_at": datetime.now().isoformat()
        }
        if self.uploader.upload_json(metadata, f"{r2_base}/metadata.json"):
            logger.info(f"✅ Metadata uploaded")
        else:
            logger.error(f"❌ Metadata upload failed!")
        
        # Mark complete
        self.uploader.upload_json(
            {"completed_at": datetime.now().isoformat(), "episodes": success},
            f"{r2_base}/complete.json"
        )
        
        # Save to Supabase - use correct schema!
        # thumbnail_url uses Railway stream API for proper CORS headers
        stream_base = "https://tender-connection-production-246f.up.railway.app/api/stream"
        thumbnail_url = f"{stream_base}/{r2_base}/cover.jpg"
        
        db_data = {
            "flickreels_id": drama_id,
            "title": title,
            "synopsis": drama.get("description", ""),
            "thumbnail_url": thumbnail_url,
            "total_episodes": len(episodes),
            "r2_folder": f"{clean_title} ({drama_id})",
            "is_published": True  # AUTO-PUBLISH for Indonesian dramas!
        }
        self.supabase.insert_drama(db_data)
        
        # Track progress
        self._save_progress(drama_id)
        with self.stats_lock:
            self.stats["dramas_processed"] += 1
        
        logger.info(f"✅ {title} COMPLETE!")
    
    def discover_and_scrape(self, limit=None, fresh=False):
        """Discover Indonesian dramas and scrape them"""
        if fresh:
            self._clear_progress()
        
        logger.info("\n" + "=" * 60)
        logger.info("INDONESIAN BATCH SCRAPER - Railway Edition")
        logger.info("Using /navigationColumn for REAL Indonesian content")
        logger.info("=" * 60 + "\n")
        
        # Discover dramas
        all_dramas = {}
        page = 1
        empty_count = 0
        
        while empty_count < 3:
            logger.info(f"Discovering page {page}...")
            dramas = self.api.get_indonesian_dramas(page=page)
            
            if not dramas:
                empty_count += 1
            else:
                empty_count = 0
                for d in dramas:
                    if d["id"] not in all_dramas:
                        all_dramas[d["id"]] = d
            
            page += 1
            
            # Early exit if we have enough
            if limit and len(all_dramas) >= limit:
                break
        
        logger.info(f"Discovered {len(all_dramas)} Indonesian dramas")
        
        # Apply limit
        dramas_to_scrape = list(all_dramas.values())
        if limit:
            dramas_to_scrape = dramas_to_scrape[:limit]
        
        # Filter already scraped
        dramas_to_scrape = [d for d in dramas_to_scrape if d["id"] not in self.scraped_ids]
        logger.info(f"Will scrape {len(dramas_to_scrape)} new dramas")
        
        # Scrape each drama
        for i, drama in enumerate(dramas_to_scrape):
            logger.info(f"\n[{i+1}/{len(dramas_to_scrape)}] Starting {drama['title']}...")
            self.scrape_drama(drama)
        
        # Final report
        elapsed = time.time() - self.stats["start_time"]
        logger.info(f"\n{'='*60}")
        logger.info("BATCH SCRAPE COMPLETE!")
        logger.info(f"  Dramas: {self.stats['dramas_processed']}")
        logger.info(f"  Episodes: {self.stats['episodes_uploaded']}")
        logger.info(f"  Time: {elapsed/60:.1f} minutes")
        if self.stats['dramas_processed'] > 0:
            logger.info(f"  Avg: {elapsed/60/self.stats['dramas_processed']:.1f} min/drama")
        logger.info(f"{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indonesian Batch Scraper")
    parser.add_argument("--limit", type=int, default=None, help="Limit dramas to scrape")
    parser.add_argument("--fresh", action="store_true", help="Clear progress and restart")
    args = parser.parse_args()
    
    scraper = IndonesianBatchScraper()
    scraper.discover_and_scrape(limit=args.limit, fresh=args.fresh)
