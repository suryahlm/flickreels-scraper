"""
FlickReels R2 Scraper
=====================

Scraper untuk download drama FlickReels dan upload ke Cloudflare R2.

Features:
- Download semua drama dari FlickReels API
- Download video HLS dan convert ke MP4 (opsional)
- Upload ke Cloudflare R2
- Resume capability (skip already downloaded)
- Rate limiting untuk avoid detection

Usage:
    python flickreels_r2_scraper.py --mode=metadata  # Download metadata only
    python flickreels_r2_scraper.py --mode=full      # Download everything
    python flickreels_r2_scraper.py --drama=2858     # Download specific drama

Environment Variables (or use config below):
    R2_ACCOUNT_ID
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET_NAME
    FLICKREELS_TOKEN
"""

import os
import json
import time
import hashlib
import hmac
import random
import string
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import argparse

# Try to import boto3 for R2
try:
    import boto3
    from botocore.config import Config
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("WARNING: boto3 not installed. Run: pip install boto3")

# ============================================================================
# CONFIGURATION
# ============================================================================

# R2 Configuration
R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "asiandrama-cdn"),
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com"
}

# FlickReels API Configuration
FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.getenv("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0",
    "user_agent": "MyUserAgent"
}

# Default device params
DEFAULT_DEVICE_PARAMS = {
    "main_package_id": 100,
    "googleAdId": "",
    "device_id": "0d209b4d4009b44c",
    "device_sign": "3af3b323830984d797d4d623af999126f3ec0d3071f69532c2c4a27b67b89e74",
    "apps_flyer_uid": "1769621528308-5741215934785896746",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "language_id": "6",
    "countryCode": "ID"
}

# Scraping settings
SCRAPE_SETTINGS = {
    "request_delay": 0.2,  # seconds between requests
    "max_retries": 3,
    "timeout": 30,
    "workers": 3,  # parallel downloads
    "r2_prefix": "flickreels"  # folder in R2 bucket
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('flickreels_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# SIGNING ALGORITHM
# ============================================================================

def method_d(body_json: str) -> str:
    """Process JSON body into sorted key-value string for signing."""
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
    """Generate HmacSHA256 sign for FlickReels API."""
    body_json = json.dumps(body, separators=(',', ':'))
    str_d = method_d(body_json)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    sign = hmac.new(
        FLICKREELS_CONFIG["secret_key"].encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return sign

def generate_nonce(length: int = 32) -> str:
    """Generate random alphanumeric nonce."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ============================================================================
# API CLIENT
# ============================================================================

class FlickReelsAPI:
    """FlickReels API Client with auto-signing."""
    
    def __init__(self, token: str = None):
        self.token = token or FLICKREELS_CONFIG["token"]
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": FLICKREELS_CONFIG["user_agent"],
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip"
        })
    
    def _request(self, endpoint: str, extra_body: dict = None) -> dict:
        """Make signed API request."""
        body = {**DEFAULT_DEVICE_PARAMS, **(extra_body or {})}
        timestamp = str(int(time.time()))
        nonce = generate_nonce()
        sign = generate_sign(body, timestamp, nonce)
        
        headers = {
            "token": self.token,
            "sign": sign,
            "timestamp": timestamp,
            "nonce": nonce
        }
        
        url = f"{FLICKREELS_CONFIG['base_url']}{endpoint}"
        
        for attempt in range(SCRAPE_SETTINGS["max_retries"]):
            try:
                response = self.session.post(
                    url, 
                    json=body, 
                    headers=headers,
                    timeout=SCRAPE_SETTINGS["timeout"]
                )
                return response.json()
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt+1}): {e}")
                time.sleep(1)
        
        return {"status_code": -1, "msg": "Max retries exceeded"}
    
    def get_all_dramas(self, nav_ids: List[int] = None) -> Dict[str, dict]:
        """Get all dramas from multiple navigation IDs."""
        if nav_ids is None:
            nav_ids = list(range(1, 601))
        
        all_dramas = {}
        
        for nav_id in nav_ids:
            result = self._request("/app/playlet/navigationColumn", {
                "navigation_id": nav_id,
                "page": 1,
                "page_size": 100
            })
            
            if result.get("status_code") == 1:
                data = result.get("data", [])
                for col in data if isinstance(data, list) else []:
                    for drama in col.get("list", []):
                        pid = str(drama.get("playlet_id", ""))
                        if pid and pid not in all_dramas:
                            all_dramas[pid] = {
                                "playlet_id": pid,
                                "title": drama.get("title"),
                                "cover_url": drama.get("cover_url") or drama.get("cover"),
                                "chapter_total": drama.get("chapter_total"),
                                "is_vip": drama.get("is_vip", 0),
                                "nav_id": nav_id
                            }
            
            if nav_id % 50 == 0:
                logger.info(f"Scan progress: nav_id {nav_id}, dramas: {len(all_dramas)}")
            
            time.sleep(SCRAPE_SETTINGS["request_delay"])
        
        return all_dramas
    
    def get_episodes(self, playlet_id: str) -> List[dict]:
        """Get episode list for a drama."""
        result = self._request("/app/playlet/chapterList", {
            "playlet_id": playlet_id,
            "chapter_type": -1,
            "auto_unlock": False,
            "fragmentPosition": 0,
            "show_type": 0,
            "source": 1,
            "vip_btn_scene": '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        })
        
        if result.get("status_code") != 1:
            logger.error(f"Failed to get episodes for {playlet_id}: {result.get('msg')}")
            return []
        
        data = result.get("data", {})
        episode_list = data.get("list", []) if isinstance(data, dict) else []
        
        episodes = []
        for ep in episode_list:
            episodes.append({
                "chapter_id": ep.get("chapter_id"),
                "title": ep.get("chapter_title") or ep.get("title"),
                "chapter_num": ep.get("chapter_num") or ep.get("chapter_number"),
                "duration": ep.get("chapter_duration") or ep.get("duration"),
                "cover_url": ep.get("chapter_cover") or ep.get("cover_url"),
                "is_free": ep.get("is_free", 0) == 1,
                "is_vip": ep.get("is_vip", 0) == 1,
                "cost_coin": ep.get("cost_coin", 0)
            })
        
        return episodes
    
    def get_stream_url(self, playlet_id: str, chapter_id: str) -> Optional[dict]:
        """Get HLS stream URL for an episode."""
        result = self._request("/app/playlet/play", {
            "playlet_id": playlet_id,
            "chapter_id": chapter_id,
            "chapter_type": 0,
            "auto_unlock": False,
            "fragmentPosition": 0,
            "show_type": 0,
            "source": 1,
            "vip_btn_scene": '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        })
        
        if result.get("status_code") != 1:
            logger.error(f"Failed to get stream URL: {result.get('msg')}")
            return None
        
        data = result.get("data", {})
        hls_url = data.get("hls_url") or data.get("hls")
        
        if not hls_url:
            return None
        
        return {
            "hls_url": hls_url,
            "title": data.get("chapter_title"),
            "duration": data.get("total_duration"),
            "hls_timeout": data.get("hls_timeout"),
            "is_vip_unlock": data.get("is_vip_unlock"),
            "play_type": data.get("e_play_type")
        }

# ============================================================================
# R2 STORAGE
# ============================================================================

class R2Storage:
    """Cloudflare R2 storage client."""
    
    def __init__(self):
        if not HAS_BOTO3:
            raise ImportError("boto3 is required. Install with: pip install boto3")
        
        self.client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG["endpoint_url"],
            aws_access_key_id=R2_CONFIG["access_key_id"],
            aws_secret_access_key=R2_CONFIG["secret_access_key"],
            config=Config(signature_version='s3v4')
        )
        self.bucket = R2_CONFIG["bucket_name"]
        self.prefix = SCRAPE_SETTINGS["r2_prefix"]
    
    def _key(self, path: str) -> str:
        """Generate full R2 key with prefix."""
        return f"{self.prefix}/{path}"
    
    def exists(self, path: str) -> bool:
        """Check if object exists in R2."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(path))
            return True
        except:
            return False
    
    def upload_json(self, path: str, data: dict) -> bool:
        """Upload JSON data to R2."""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=self._key(path),
                Body=json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upload JSON to {path}: {e}")
            return False
    
    def upload_file(self, path: str, file_path: str, content_type: str = None) -> bool:
        """Upload file to R2."""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.client.upload_file(
                file_path,
                self.bucket,
                self._key(path),
                ExtraArgs=extra_args
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upload file to {path}: {e}")
            return False
    
    def upload_from_url(self, path: str, url: str, content_type: str = None) -> bool:
        """Download from URL and upload to R2."""
        try:
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            self.client.put_object(
                Bucket=self.bucket,
                Key=self._key(path),
                Body=response.content,
                ContentType=content_type or response.headers.get('Content-Type', 'application/octet-stream')
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upload from URL to {path}: {e}")
            return False
    
    def get_public_url(self, path: str) -> str:
        """Get public URL for object (requires public bucket or custom domain)."""
        # Adjust this based on your R2 public access configuration
        return f"https://{self.bucket}.r2.dev/{self._key(path)}"

# ============================================================================
# SCRAPER
# ============================================================================

class FlickReelsScraper:
    """Main scraper orchestrator."""
    
    def __init__(self):
        self.api = FlickReelsAPI()
        self.storage = R2Storage() if HAS_BOTO3 else None
        self.stats = {
            "dramas_processed": 0,
            "episodes_processed": 0,
            "errors": 0,
            "start_time": None
        }
    
    def scrape_metadata_only(self, drama_ids: List[str] = None):
        """Scrape and upload metadata only (no video download)."""
        self.stats["start_time"] = datetime.now()
        
        # Get all dramas if not specified
        if drama_ids is None:
            logger.info("Fetching all dramas...")
            dramas = self.api.get_all_dramas()
            drama_ids = list(dramas.keys())
            
            # Save drama index
            if self.storage:
                self.storage.upload_json("dramas/index.json", {
                    "total": len(dramas),
                    "updated_at": datetime.now().isoformat(),
                    "dramas": dramas
                })
                logger.info(f"Uploaded drama index with {len(dramas)} dramas")
        else:
            dramas = {}
        
        # Process each drama
        for pid in drama_ids:
            try:
                self._process_drama_metadata(pid, dramas.get(pid, {}))
                self.stats["dramas_processed"] += 1
                
                if self.stats["dramas_processed"] % 10 == 0:
                    logger.info(f"Progress: {self.stats['dramas_processed']}/{len(drama_ids)} dramas")
                
            except Exception as e:
                logger.error(f"Error processing drama {pid}: {e}")
                self.stats["errors"] += 1
            
            time.sleep(SCRAPE_SETTINGS["request_delay"])
        
        self._log_stats()
    
    def _process_drama_metadata(self, playlet_id: str, drama_info: dict):
        """Process single drama metadata."""
        # Get episodes
        episodes = self.api.get_episodes(playlet_id)
        
        # Build metadata
        metadata = {
            "playlet_id": playlet_id,
            "title": drama_info.get("title", "Unknown"),
            "cover_url": drama_info.get("cover_url"),
            "chapter_total": len(episodes),
            "episodes": episodes,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Upload metadata
        if self.storage:
            self.storage.upload_json(f"dramas/{playlet_id}/metadata.json", metadata)
            
            # Upload cover image
            cover_url = drama_info.get("cover_url")
            if cover_url:
                self.storage.upload_from_url(
                    f"dramas/{playlet_id}/cover.jpg",
                    cover_url,
                    "image/jpeg"
                )
        
        self.stats["episodes_processed"] += len(episodes)
    
    def scrape_full(self, drama_ids: List[str] = None, include_videos: bool = True):
        """Full scrape including video URLs."""
        self.stats["start_time"] = datetime.now()
        
        # Get all dramas if not specified
        if drama_ids is None:
            logger.info("Fetching all dramas...")
            dramas = self.api.get_all_dramas()
            drama_ids = list(dramas.keys())
        else:
            dramas = {pid: {} for pid in drama_ids}
        
        logger.info(f"Starting full scrape of {len(drama_ids)} dramas")
        
        for pid in drama_ids:
            try:
                self._process_drama_full(pid, dramas.get(pid, {}), include_videos)
                self.stats["dramas_processed"] += 1
                
                if self.stats["dramas_processed"] % 5 == 0:
                    logger.info(f"Progress: {self.stats['dramas_processed']}/{len(drama_ids)} dramas")
                
            except Exception as e:
                logger.error(f"Error processing drama {pid}: {e}")
                self.stats["errors"] += 1
            
            time.sleep(SCRAPE_SETTINGS["request_delay"])
        
        self._log_stats()
    
    def _process_drama_full(self, playlet_id: str, drama_info: dict, include_videos: bool):
        """Process single drama with videos."""
        # Check if already processed
        if self.storage and self.storage.exists(f"dramas/{playlet_id}/complete.json"):
            logger.info(f"Skipping {playlet_id} - already complete")
            return
        
        # Get episodes
        episodes = self.api.get_episodes(playlet_id)
        
        episode_data = []
        for ep in episodes:
            chapter_id = ep.get("chapter_id")
            if not chapter_id:
                continue
            
            ep_info = {**ep}
            
            if include_videos:
                # Get stream URL
                stream = self.api.get_stream_url(playlet_id, chapter_id)
                if stream:
                    ep_info["hls_url"] = stream.get("hls_url")
                    ep_info["hls_timeout"] = stream.get("hls_timeout")
                    
                    # Store HLS URL reference (not downloading actual video)
                    if self.storage:
                        self.storage.upload_json(
                            f"dramas/{playlet_id}/episodes/{chapter_id}.json",
                            ep_info
                        )
                
                time.sleep(SCRAPE_SETTINGS["request_delay"])
            
            episode_data.append(ep_info)
            self.stats["episodes_processed"] += 1
        
        # Build complete metadata
        metadata = {
            "playlet_id": playlet_id,
            "title": drama_info.get("title", "Unknown"),
            "cover_url": drama_info.get("cover_url"),
            "chapter_total": len(episode_data),
            "episodes": episode_data,
            "scraped_at": datetime.now().isoformat()
        }
        
        # Upload complete marker
        if self.storage:
            self.storage.upload_json(f"dramas/{playlet_id}/metadata.json", metadata)
            self.storage.upload_json(f"dramas/{playlet_id}/complete.json", {
                "completed_at": datetime.now().isoformat()
            })
    
    def _log_stats(self):
        """Log scraping statistics."""
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info(f"Dramas processed: {self.stats['dramas_processed']}")
        logger.info(f"Episodes processed: {self.stats['episodes_processed']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Time elapsed: {elapsed:.1f} seconds")
        logger.info("=" * 60)

# ============================================================================
# MAIN
# ============================================================================

def get_batch_drama_ids(all_drama_ids: List[str], batch: int) -> List[str]:
    """
    Split drama IDs into 4 batches for safe scraping.
    
    Batch 1: Drama 1-600 (index 0-599)
    Batch 2: Drama 601-1200 (index 600-1199)
    Batch 3: Drama 1201-1800 (index 1200-1799)
    Batch 4: Drama 1801-end (index 1800+)
    """
    total = len(all_drama_ids)
    batch_size = total // 4
    
    if batch == 1:
        return all_drama_ids[0:batch_size]
    elif batch == 2:
        return all_drama_ids[batch_size:batch_size*2]
    elif batch == 3:
        return all_drama_ids[batch_size*2:batch_size*3]
    elif batch == 4:
        return all_drama_ids[batch_size*3:]
    else:
        return all_drama_ids


def main():
    parser = argparse.ArgumentParser(description="FlickReels R2 Scraper")
    parser.add_argument("--mode", choices=["metadata", "full", "test"], default="test",
                        help="Scraping mode")
    parser.add_argument("--drama", type=str, help="Specific drama ID to scrape")
    parser.add_argument("--limit", type=int, help="Limit number of dramas")
    parser.add_argument("--batch", type=int, choices=[1, 2, 3, 4],
                        help="Batch number (1-4) for safe 4-day scraping. Each batch ~600 dramas.")
    
    args = parser.parse_args()
    
    scraper = FlickReelsScraper()
    
    if args.mode == "test":
        # Test mode - just verify everything works
        logger.info("=== TEST MODE ===")
        
        # Test API
        logger.info("Testing API...")
        api = FlickReelsAPI()
        result = api._request("/app/playlet/hotRank", {"rank_type": 0})
        if result.get("status_code") == 1:
            logger.info("✓ API connection OK")
        else:
            logger.error("✗ API connection failed")
            return
        
        # Test R2
        if HAS_BOTO3:
            logger.info("Testing R2...")
            storage = R2Storage()
            if storage.upload_json("test/connection.json", {"test": True, "time": datetime.now().isoformat()}):
                logger.info("✓ R2 connection OK")
            else:
                logger.error("✗ R2 connection failed")
        
        # Test single drama
        logger.info("Testing single drama scrape...")
        episodes = api.get_episodes("2858")
        logger.info(f"✓ Got {len(episodes)} episodes for drama 2858")
        
        if episodes:
            stream = api.get_stream_url("2858", episodes[0]["chapter_id"])
            if stream and stream.get("hls_url"):
                logger.info(f"✓ Got stream URL: {stream['hls_url'][:60]}...")
            else:
                logger.warning("✗ Could not get stream URL (might need VIP)")
        
        logger.info("=== TEST COMPLETE ===")
    
    elif args.mode == "metadata":
        drama_ids = [args.drama] if args.drama else None
        if drama_ids is None:
            # Get all dramas first
            logger.info("Fetching drama list...")
            dramas = scraper.api.get_all_dramas()
            drama_ids = list(dramas.keys())
            
            # Apply batch filter if specified
            if args.batch:
                drama_ids = get_batch_drama_ids(drama_ids, args.batch)
                logger.info(f"BATCH {args.batch}: Processing {len(drama_ids)} dramas")
            
            # Apply limit if specified
            if args.limit:
                drama_ids = drama_ids[:args.limit]
        
        scraper.scrape_metadata_only(drama_ids)
    
    elif args.mode == "full":
        drama_ids = [args.drama] if args.drama else None
        if drama_ids is None:
            # Get all dramas first
            logger.info("Fetching drama list...")
            dramas = scraper.api.get_all_dramas()
            all_drama_ids = list(dramas.keys())
            logger.info(f"Total dramas found: {len(all_drama_ids)}")
            
            # Apply batch filter if specified
            if args.batch:
                drama_ids = get_batch_drama_ids(all_drama_ids, args.batch)
                logger.info(f"=== BATCH {args.batch} MODE ===")
                logger.info(f"Processing {len(drama_ids)} dramas (out of {len(all_drama_ids)} total)")
            else:
                drama_ids = all_drama_ids
                logger.info("=== FULL MODE (no batch) ===")
            
            # Apply limit if specified
            if args.limit:
                drama_ids = drama_ids[:args.limit]
                logger.info(f"Limited to {len(drama_ids)} dramas")
        
        logger.info(f"Starting scrape of {len(drama_ids)} dramas...")
        scraper.scrape_full(drama_ids)

if __name__ == "__main__":
    main()

