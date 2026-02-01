"""
FlickReels Indonesian Scraper - FIXED VERSION
=============================================

FIXES APPLIED:
1. ✅ Episodes stored at root level (no /episodes/ subdir)
2. ✅ Cover image downloaded and uploaded
3. ✅ Indonesian language only (language_id=6)
4. ✅ Folder naming: {Title} ({ID})

Usage:
    railway run python indonesian_scraper_fixed.py --drama=2858 --episodes=100
"""

import os
import json
import time
import hashlib
import hmac
import random
import string
import argparse
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore, Lock

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

# INDONESIAN ONLY! language_id = 6
DEFAULT_BODY_PARAMS = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "54635c70fbd4b9ece7bcac55af30c6a48a63a8fedcf7f61c4a54cd8604ab4851",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID",
    "language_id": "6"  # INDONESIAN ONLY!
}

CONCURRENT_CONFIG = {
    "max_concurrent_episodes": 8,
    "max_concurrent_segments": 4,
    "max_requests_per_second": 12,
    "retry_attempts": 5,
    "request_timeout": 60,
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
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
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                time.sleep(self.min_interval - time_since_last)
            self.last_call = time.time()

rate_limiter = RateLimiter(CONCURRENT_CONFIG["max_requests_per_second"])

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
    
    def _request(self, endpoint, extra_body=None, retries=3):
        for attempt in range(retries):
            try:
                rate_limiter.acquire()
                body = {**DEFAULT_BODY_PARAMS, **(extra_body or {})}
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
                    logger.error(f"Request failed: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None
    
    def get_drama_detail(self, drama_id):
        result = self._request("/v1/video/playletDetail", {"playlet_id": drama_id})
        if not result or result.get("status_code") != 1:
            return None
        return result.get("data", {})
    
    def get_stream_url(self, drama_id, chapter_id):
        result = self._request("/v2/video/getVideoPlayUrl", {
            "playlet_id": drama_id,
            "chapter_id": chapter_id
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

# ============================================================================
# FIXED SCRAPER
# ============================================================================

class IndonesianScraper:
    """Fixed scraper with all 3 issues resolved"""
    
    def __init__(self):
        self.api = FlickReelsAPI()
        self.uploader = R2Uploader()
        self.stats = {
            "episodes_done": 0,
            "episodes_failed": 0,
            "segments_uploaded": 0,
        }
        self.lock = Lock()
    
    def parse_m3u8(self, content, base_url):
        segments = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.endswith('.ts') or '.ts?' in line:
                if not line.startswith('http'):
                    from urllib.parse import urljoin
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
    
    def scrape_cover(self, cover_url, r2_path):
        """FIX #2: Download and upload cover image"""
        if not cover_url:
            logger.warning("No cover URL provided")
            return False
        
        try:
            logger.info(f"Downloading cover from {cover_url[:50]}...")
            response = requests.get(cover_url, timeout=30)
            response.raise_for_status()
            
            if len(response.content) < 1000:
                logger.warning("Cover image too small, skipping")
                return False
            
            # FIX: Upload cover at ROOT level (not in /episodes/)
            r2_key = f"{r2_path}/cover.jpg"
            if self.uploader.upload_bytes(response.content, r2_key, 'image/jpeg'):
                logger.info(f"✅ Cover uploaded: {r2_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cover download failed: {e}")
            return False
    
    def scrape_episode(self, drama_id, episode_num, chapter_id, r2_path):
        """FIX #1: Store episodes at ROOT level (no /episodes/ subdir)"""
        try:
            logger.info(f"[EP {episode_num}] Starting...")
            
            hls_url = self.api.get_stream_url(drama_id, chapter_id)
            if not hls_url:
                logger.error(f"[EP {episode_num}] Failed to get HLS URL")
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
                logger.warning(f"[EP {episode_num}] No segments found")
                return False
            
            logger.info(f"[EP {episode_num}] Uploading {len(segments)} segments...")
            
            episode_prefix = f"ep_{episode_num:03d}"
            
            # FIX #1: Store at ROOT level, NOT in /episodes/ subfolder!
            r2_episode_dir = r2_path  # Direct path, no /episodes/ added
            
            # Upload segments concurrently
            with ThreadPoolExecutor(max_workers=CONCURRENT_CONFIG["max_concurrent_segments"]) as executor:
                futures = []
                for i, segment_url in enumerate(segments):
                    r2_key = f"{r2_episode_dir}/{episode_prefix}_{i:04d}.ts"
                    future = executor.submit(
                        self.uploader.upload_stream,
                        segment_url, r2_key, "video/mp2t"
                    )
                    futures.append(future)
                
                success = sum(1 for f in futures if f.result())
            
            if success == 0:
                logger.error(f"[EP {episode_num}] All segments failed")
                return False
            
            # Upload rewritten m3u8
            rewritten = self.rewrite_m3u8(m3u8_content, episode_prefix)
            m3u8_key = f"{r2_episode_dir}/{episode_prefix}.m3u8"
            self.uploader.upload_bytes(rewritten.encode(), m3u8_key, 'application/vnd.apple.mpegurl')
            
            with self.lock:
                self.stats["episodes_done"] += 1
                self.stats["segments_uploaded"] += success
            
            logger.info(f"[EP {episode_num}] ✅ Done ({success}/{len(segments)} segments)")
            return True
            
        except Exception as e:
            logger.error(f"[EP {episode_num}] Error: {e}")
            with self.lock:
                self.stats["episodes_failed"] += 1
            return False
    
    def scrape_drama(self, drama_id, max_episodes=100):
        """Scrape Indonesian drama with all fixes"""
        logger.info(f"="*60)
        logger.info(f"SCRAPING DRAMA {drama_id}")
        logger.info(f"="*60)
        
        # Get drama details
        detail = self.api.get_drama_detail(drama_id)
        if not detail:
            logger.error("Failed to get drama details")
            return False
        
        title = detail.get("title", f"Drama {drama_id}")
        cover_url = detail.get("cover_url") or detail.get("thumbnail_url")
        chapters = detail.get("chapter_list", [])
        
        # FIX #3: Verify language is Indonesian
        language_name = detail.get("language_name", "")
        if language_name and "indo" not in language_name.lower():
            logger.warning(f"⚠️ Language '{language_name}' may not be Indonesian!")
        
        logger.info(f"Title: {title}")
        logger.info(f"Language: {language_name}")
        logger.info(f"Episodes: {len(chapters)}")
        logger.info(f"Cover URL: {cover_url[:50] if cover_url else 'None'}...")
        
        # Create R2 path with {Title} ({ID}) format
        safe_title = "".join(c for c in title if c.isalnum() or c in ' _-').strip()
        r2_path = f"flickreels/{safe_title} ({drama_id})"
        
        logger.info(f"R2 Path: {r2_path}")
        
        # FIX #2: Download cover FIRST
        if cover_url:
            self.scrape_cover(cover_url, r2_path)
        else:
            logger.warning("No cover URL available")
        
        # Upload metadata
        metadata = {
            "id": drama_id,
            "title": title,
            "cover_url": cover_url,
            "total_episodes": len(chapters),
            "language": language_name,
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.uploader.upload_json(metadata, f"{r2_path}/metadata.json")
        
        # Scrape episodes concurrently
        episodes_to_scrape = chapters[:max_episodes]
        logger.info(f"Scraping {len(episodes_to_scrape)} episodes...")
        
        with ThreadPoolExecutor(max_workers=CONCURRENT_CONFIG["max_concurrent_episodes"]) as executor:
            futures = []
            for i, chapter in enumerate(episodes_to_scrape, 1):
                chapter_id = str(chapter.get("id", ""))
                if chapter_id:
                    future = executor.submit(
                        self.scrape_episode,
                        drama_id, i, chapter_id, r2_path
                    )
                    futures.append(future)
            
            # Wait for all
            for f in futures:
                f.result()
        
        # Upload complete marker
        complete_data = {
            "id": drama_id,
            "title": title,
            "total_episodes": len(episodes_to_scrape),
            "episodes_done": self.stats["episodes_done"],
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.uploader.upload_json(complete_data, f"{r2_path}/complete.json")
        
        logger.info(f"\n" + "="*60)
        logger.info(f"SCRAPING COMPLETE!")
        logger.info(f"  Episodes: {self.stats['episodes_done']}/{len(episodes_to_scrape)}")
        logger.info(f"  Segments: {self.stats['segments_uploaded']}")
        logger.info(f"  Failed: {self.stats['episodes_failed']}")
        logger.info(f"="*60)
        
        return self.stats["episodes_done"] > 0

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Indonesian Drama Scraper - FIXED')
    parser.add_argument('--drama', type=str, required=True, help='Drama ID to scrape')
    parser.add_argument('--episodes', type=int, default=100, help='Max episodes')
    args = parser.parse_args()
    
    if not FLICKREELS_CONFIG["token"]:
        logger.error("FLICKREELS_TOKEN not set!")
        return
    
    scraper = IndonesianScraper()
    scraper.scrape_drama(args.drama, args.episodes)

if __name__ == "__main__":
    main()
