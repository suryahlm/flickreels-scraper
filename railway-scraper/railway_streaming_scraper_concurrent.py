"""
FlickReels → R2 Concurrent Streaming Scraper
============================================

12 CONCURRENT EPISODES - PRODUCTION READY!
- Download 12 episodes simultaneously
- Rate limiting to avoid API ban
- Error recovery with retries
- Progress tracking
- Safe for Railway Pro deployment

Usage:
    python railway_streaming_scraper_concurrent.py --drama=2858 --episodes=100
"""

import os
import json
import time
import hashlib
import hmac
import random
import string
import logging
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore, Lock

import requests

try:
    import boto3
    from botocore.config import Config
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("ERROR: boto3 not installed. Run: pip install boto3")
    exit(1)

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

# CONCURRENT CONFIGURATION (Railway Pro optimized!)
CONCURRENT_CONFIG = {
    "max_concurrent_episodes": 12,          # 12 episodes at once (sweet spot!)
    "max_concurrent_segments": 4,           # 4 segments per episode
    "max_requests_per_second": 15,          # Rate limit: 15 req/sec
    "retry_attempts": 5,                    # Retry failed downloads
    "retry_delay": 2,                       # Start with 2s delay
    "request_timeout": 60,                  # 60s timeout per request
}

DEFAULT_BODY_PARAMS = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID",
    "language_id": "6"
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
    """Thread-safe rate limiter to prevent API abuse"""
    
    def __init__(self, max_per_second=15):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_call = 0
        self.lock = Lock()
    
    def acquire(self):
        """Wait if necessary to maintain rate limit"""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_call = time.time()

# Global rate limiter
rate_limiter = RateLimiter(max_per_second=CONCURRENT_CONFIG["max_requests_per_second"])

# ============================================================================
# API SIGNING (same as before)
# ============================================================================

def generate_nonce(length: int = 32) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def method_d(body_json: str) -> str:
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

def generate_sign(body: dict, timestamp: str, nonce: str) -> str:
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
# API CLIENT (with retry logic)
# ============================================================================

class FlickReelsAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
    
    def _request_with_retry(self, endpoint: str, extra_body: dict = None, retries=3) -> dict:
        """API request with exponential backoff retry"""
        for attempt in range(retries):
            try:
                # Rate limit
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
                
                # Check for rate limiting
                if response.status_code == 429:
                    wait = (2 ** attempt) * 2  # Exponential backoff
                    logger.warning(f"Rate limited! Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.Timeout:
                wait = 2 ** attempt
                logger.warning(f"Timeout on attempt {attempt+1}/{retries}, waiting {wait}s...")
                time.sleep(wait)
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"API request failed after {retries} attempts: {e}")
                    return {"status_code": -1, "msg": str(e)}
                time.sleep(2 ** attempt)
        
        return {"status_code": -1, "msg": "Max retries exceeded"}
    
    def get_episodes(self, playlet_id: str) -> List[dict]:
        """Get episode list for drama"""
        result = self._request_with_retry("/app/playlet/chapterList", {"playlet_id": playlet_id})
        
        if result.get("status_code") != 1:
            return []
        
        data = result.get("data", {})
        episodes = []
        for ep in data.get("list", []):
            episodes.append({
                "chapter_id": ep.get("chapter_id"),
                "title": ep.get("title", f"EP.{ep.get('sort', 1)}"),
                "chapter_num": ep.get("sort", 1)
            })
        
        return episodes
    
    def get_drama_details(self, playlet_id: str) -> Optional[dict]:
        """Get drama details including title - uses chapterList endpoint"""
        result = self._request_with_retry("/app/playlet/chapterList", {"playlet_id": playlet_id})
        
        if result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        return {
            "playlet_id": playlet_id,
            "title": data.get("title", f"Drama_{playlet_id}"),
            "cover": data.get("cover") or data.get("process_cover"),
            "description": "",  # Not available in chapterList
            "total_chapter": len(data.get("list", [])),
            "tags": []  # Will be collected from play endpoint
        }
    
    def get_stream_url(self, playlet_id: str, chapter_id: str) -> Optional[dict]:
        """Get fresh HLS URL and tags for episode"""
        result = self._request_with_retry("/app/playlet/play", {
            "playlet_id": playlet_id,
            "chapter_id": chapter_id
        })
        
        if result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        hls_url = data.get("hls_url") or data.get("hls")
        
        if not hls_url:
            return None
        
        tags = [t.get("tag_name") for t in data.get("tag_list", [])]
        
        return {
            "hls_url": hls_url,
            "tags": tags,
            "duration": data.get("total_duration")
        }

# ============================================================================
# R2 UPLOADER (thread-safe)
# ============================================================================

class R2StreamUploader:
    """Thread-safe R2 uploader"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG["endpoint_url"],
            aws_access_key_id=R2_CONFIG["access_key_id"],
            aws_secret_access_key=R2_CONFIG["secret_access_key"],
            config=Config(signature_version='s3v4')
        )
        self.bucket = R2_CONFIG["bucket_name"]
    
    def upload_stream_with_retry(self, url: str, r2_key: str, content_type: str = None, retries=3) -> bool:
        """Upload with retry logic"""
        for attempt in range(retries):
            try:
                rate_limiter.acquire()
                
                response = requests.get(url, stream=True, timeout=CONCURRENT_CONFIG["request_timeout"])
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
                    logger.error(f"Upload failed for {r2_key} after {retries} attempts: {e}")
                    return False
                wait = 2 ** attempt
                logger.warning(f"Upload retry {attempt+1}/{retries} in {wait}s...")
                time.sleep(wait)
        
        return False
    
    def upload_bytes(self, content: bytes, r2_key: str, content_type: str = None) -> bool:
        """Upload bytes directly to R2"""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=r2_key,
                Body=content,
                ContentType=content_type or 'application/octet-stream'
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed for {r2_key}: {e}")
            return False
    
    def upload_json(self, data: dict, r2_key: str) -> bool:
        """Upload JSON data to R2"""
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        return self.upload_bytes(json_bytes, r2_key, 'application/json')

# ============================================================================
# CONCURRENT SCRAPER
# ============================================================================

class ConcurrentStreamingScraper:
    """Concurrent scraper with 12 parallel episodes"""
    
    def __init__(self):
        self.api = FlickReelsAPI()
        self.uploader = R2StreamUploader()
        self.stats = {
            "episodes_processed": 0,
            "episodes_failed": 0,
            "segments_uploaded": 0,
            "errors": 0,
            "start_time": time.time()
        }
        self.stats_lock = Lock()
    
    def parse_m3u8(self, content: str, base_url: str) -> List[str]:
        """Parse m3u8 and extract segment URLs"""
        segments = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            if line.endswith('.ts') or '.ts?' in line:
                if not line.startswith('http'):
                    from urllib.parse import urljoin
                    segment_url = urljoin(base_url, line)
                else:
                    segment_url = line
                segments.append(segment_url)
        
        return segments
    
    def rewrite_m3u8(self, content: str, episode_prefix: str) -> str:
        """Rewrite m3u8 to use R2 paths"""
        lines = content.strip().split('\n')
        new_lines = []
        segment_index = 0
        
        for line in lines:
            line = line.strip()
            if line.endswith('.ts') or '.ts?' in line:
                new_lines.append(f"{episode_prefix}_{segment_index:04d}.ts")
                segment_index += 1
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def scrape_episode(
        self,
        drama_id: str,
        episode_num: int,
        chapter_id: str,
        r2_base_path: str = None
    ) -> bool:
        """Scrape single episode (called by thread pool)"""
        try:
            logger.info(f"[EP {episode_num}] Starting...")
            
            # Get stream URL
            stream_data = self.api.get_stream_url(drama_id, chapter_id)
            if not stream_data:
                logger.error(f"[EP {episode_num}] Failed to get HLS URL")
                return False
            
            hls_url = stream_data["hls_url"]
            
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
            
            # Upload segments (with concurrency limit per episode)
            episode_prefix = f"ep_{episode_num:03d}"
            # Use provided path with title, or fallback to ID only
            if r2_base_path:
                r2_episode_dir = f"{r2_base_path}/episodes"
            else:
                r2_episode_dir = f"flickreels/{drama_id}/episodes"
            
            # Use ThreadPoolExecutor for segments (4 concurrent per episode)
            with ThreadPoolExecutor(max_workers=CONCURRENT_CONFIG["max_concurrent_segments"]) as executor:
                futures = []
                for i, segment_url in enumerate(segments):
                    r2_key = f"{r2_episode_dir}/{episode_prefix}_{i:04d}.ts"
                    future = executor.submit(
                        self.uploader.upload_stream_with_retry,
                        segment_url,
                        r2_key,
                        "video/mp2t"
                    )
                    futures.append((i, future))
                
                # Wait for all segments
                failed = 0
                for i, future in futures:
                    if future.result():
                        with self.stats_lock:
                            self.stats["segments_uploaded"] += 1
                    else:
                        failed += 1
                        logger.error(f"[EP {episode_num}] Segment {i} failed")
                
                if failed > 0:
                    logger.error(f"[EP {episode_num}] {failed}/{len(segments)} segments failed")
                    return False
            
            # Upload manifest
            new_m3u8 = self.rewrite_m3u8(m3u8_content, episode_prefix)
            r2_manifest_key = f"{r2_episode_dir}/{episode_prefix}.m3u8"
            
            if self.uploader.upload_bytes(
                new_m3u8.encode('utf-8'),
                r2_manifest_key,
                "application/vnd.apple.mpegurl"
            ):
                logger.info(f"[EP {episode_num}] ✅ Complete!")
                with self.stats_lock:
                    self.stats["episodes_processed"] += 1
                return True
            else:
                logger.error(f"[EP {episode_num}] Failed to upload manifest")
                return False
                
        except Exception as e:
            logger.error(f"[EP {episode_num}] Exception: {e}")
            with self.stats_lock:
                self.stats["errors"] += 1
            return False
    
    def scrape_drama_concurrent(self, drama_id: str, max_episodes: int = None):
        """Scrape drama with 12 concurrent episodes"""
        logger.info(f"\n{'='*60}")
        logger.info(f"CONCURRENT SCRAPER - 12 Episodes Parallel")
        logger.info(f"Drama: {drama_id}")
        logger.info(f"{'='*60}\n")
        
        # Get drama details first to get the title
        drama_details = self.api.get_drama_details(drama_id)
        if drama_details:
            drama_title = drama_details.get("title", f"Drama_{drama_id}")
            # Clean title for folder name (remove invalid chars)
            import re
            clean_title = re.sub(r'[<>:"/\\|?*]', '', drama_title)
            r2_base_path = f"flickreels/{clean_title} ({drama_id})"
            logger.info(f"Drama Title: {drama_title}")
        else:
            clean_title = f"Drama_{drama_id}"
            r2_base_path = f"flickreels/{drama_id}"
            logger.warning(f"Could not fetch drama title, using ID only")
        
        # Get episodes
        episodes = self.api.get_episodes(drama_id)
        
        if not episodes:
            logger.error("No episodes found")
            return
        
        if max_episodes:
            episodes = episodes[:max_episodes]
        
        logger.info(f"Total episodes: {len(episodes)}")
        logger.info(f"Concurrent workers: {CONCURRENT_CONFIG['max_concurrent_episodes']}")
        logger.info(f"Rate limit: {CONCURRENT_CONFIG['max_requests_per_second']} req/sec\n")
        
        # Collect tags
        all_tags = []
        for ep in episodes[:5]:  # Sample first 5 for tags
            stream_data = self.api.get_stream_url(drama_id, ep["chapter_id"])
            if stream_data and stream_data.get("tags"):
                all_tags.extend(stream_data["tags"])
        
        # Process episodes concurrently
        with ThreadPoolExecutor(max_workers=CONCURRENT_CONFIG["max_concurrent_episodes"]) as executor:
            futures = []
            
            for i, episode in enumerate(episodes):
                ep_num = i + 1
                chapter_id = episode.get("chapter_id")
                
                if not chapter_id:
                    logger.warning(f"Skipping EP {ep_num} - no chapter_id")
                    continue
                
                future = executor.submit(
                    self.scrape_episode,
                    drama_id,
                    ep_num,
                    chapter_id,
                    r2_base_path
                )
                futures.append((ep_num, future))
            
            # Wait for all episodes
            logger.info(f"\nProcessing {len(futures)} episodes concurrently...\n")
            
            for ep_num, future in futures:
                success = future.result()
                if not success:
                    with self.stats_lock:
                        self.stats["episodes_failed"] += 1
        
        # Upload metadata
        unique_tags = list(set(all_tags))
        if drama_details:
            unique_tags = list(set(drama_details.get("tags", []) + all_tags))
        
        metadata = {
            "playlet_id": drama_id,
            "title": clean_title,
            "total_episodes": len(episodes),
            "genres": unique_tags,
            "description": drama_details.get("description", "") if drama_details else "",
            "cover": drama_details.get("cover", "") if drama_details else "",
            "scraped_at": datetime.now().isoformat(),
            "episodes": episodes
        }
        
        self.uploader.upload_json(metadata, f"{r2_base_path}/metadata.json")
        self.uploader.upload_json(
            {"completed_at": datetime.now().isoformat()},
            f"{r2_base_path}/complete.json"
        )
        
        # Print stats
        elapsed = time.time() - self.stats["start_time"]
        logger.info(f"\n{'='*60}")
        logger.info("SCRAPE COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Episodes processed: {self.stats['episodes_processed']}")
        logger.info(f"Episodes failed: {self.stats['episodes_failed']}")
        logger.info(f"Segments uploaded: {self.stats['segments_uploaded']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info(f"Speed: {self.stats['episodes_processed']/(elapsed/60):.1f} episodes/min")
        logger.info(f"{'='*60}\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FlickReels Concurrent Streaming Scraper")
    parser.add_argument("--drama", type=str, required=True, help="Drama ID to scrape")
    parser.add_argument("--episodes", type=int, help="Max episodes to scrape (default: all)")
    
    args = parser.parse_args()
    
    scraper = ConcurrentStreamingScraper()
    scraper.scrape_drama_concurrent(args.drama, args.episodes)
