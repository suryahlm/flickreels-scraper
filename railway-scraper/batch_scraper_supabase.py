#!/usr/bin/env python3
"""
Batch Scraper with Supabase Integration
========================================
Scrapes dramas from discovery JSON and uploads to R2.
Inserts drama to Supabase with is_published=false (draft).

Features:
- Uses new_dramas_for_app.json as data source
- Downloads HLS streams and uploads to R2
- 12 parallel episodes per drama
- NESTED structure: ep_001/index.m3u8, ep_001/segment_0000.ts
- Inserts to Supabase for admin review
- Resume capability (skips completed dramas)
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urljoin

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("Installing boto3...")
    os.system(f"{sys.executable} -m pip install boto3")
    import boto3
    from botocore.config import Config

# Using HTTP requests directly to Supabase REST API
# This avoids the C++ compiler requirement from supabase-py

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_scraper_supabase.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# R2 Configuration
R2_CONFIG = {
    "account_id": os.environ.get("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key": os.environ.get("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket": os.environ.get("R2_BUCKET_NAME", "asiandrama-cdn"),
    "public_url": "https://pub-caa84fe6b1be065c.r2.dev"
}

# Supabase Configuration
SUPABASE_CONFIG = {
    "url": os.environ.get("SUPABASE_URL", "https://bmryonqbddbkjbtquhgu.supabase.co"),
    "key": os.environ.get("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_ANON_KEY", 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"))
}

# FlickReels API Configuration
FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.environ.get("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0"
}

# Default body for FlickReels API
FLICKREELS_BODY = {
    "main_package_id": 100,
    "googleAdId": "783978b6-0d30-438d-a58d-faf171eed978",
    "device_id": "0d209b4d4009b44c",
    "device_sign": "5af6b3970595e1df2a4be3df91ec58cbab23f04e847db0b89c33eb7eadd51f79",
    "apps_flyer_uid": "1769621528308-5741215934785896746",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "language_id": "6",
    "countryCode": "ID"
}

# ============================================================================
# FLICKREELS API SIGNING
# ============================================================================

import hashlib
import hmac
import random
import string

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
# R2 UPLOADER
# ============================================================================

class R2Uploader:
    """Handles R2 uploads with connection pooling"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_CONFIG["access_key"],
            aws_secret_access_key=R2_CONFIG["secret_key"],
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                max_pool_connections=50
            )
        )
        self.bucket = R2_CONFIG["bucket"]
        self.lock = Lock()
    
    def upload_bytes(self, data: bytes, key: str, content_type: str = "application/octet-stream") -> bool:
        """Upload bytes to R2"""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed for {key}: {e}")
            return False
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists in R2"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False
    
    def list_folders(self, prefix: str = "flickreels/") -> list:
        """List all folder names under prefix"""
        folders = set()
        paginator = self.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix, Delimiter='/'):
            for cp in page.get('CommonPrefixes', []):
                folder = cp['Prefix'].replace(prefix, '').rstrip('/')
                folders.add(folder)
        return list(folders)


# ============================================================================
# SUPABASE CLIENT (HTTP-based, no C++ dependencies)
# ============================================================================

class SupabaseClient:
    """Handles Supabase database operations via REST API"""
    
    def __init__(self):
        self.url = SUPABASE_CONFIG["url"]
        self.key = SUPABASE_CONFIG["key"]
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def drama_exists(self, flickreels_id: str) -> bool:
        """Check if drama already exists in database"""
        try:
            url = f"{self.url}/rest/v1/dramas?flickreels_id=eq.{flickreels_id}&select=id"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return len(data) > 0
            return False
        except Exception as e:
            logger.error(f"Supabase check failed: {e}")
            return False
    
    def insert_drama(self, drama_data: dict) -> bool:
        """Insert new drama with is_published=false"""
        try:
            url = f"{self.url}/rest/v1/dramas"
            resp = self.session.post(url, json=drama_data, timeout=30)
            if resp.status_code in [200, 201]:
                logger.info(f"  ✓ Inserted to Supabase (draft)")
                return True
            else:
                logger.error(f"Supabase insert failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Supabase insert failed: {e}")
            return False
    
    def insert_episodes(self, drama_db_id: str, episodes: list) -> bool:
        """Insert episodes for a drama"""
        try:
            url = f"{self.url}/rest/v1/episodes"
            for ep in episodes:
                ep['drama_id'] = drama_db_id
            resp = self.session.post(url, json=episodes, timeout=30)
            return resp.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Episodes insert failed: {e}")
            return False


# ============================================================================
# HLS DOWNLOADER - FLAT SEGMENT STRUCTURE
# ============================================================================

class HLSDownloader:
    """Downloads HLS streams and uploads to R2 with flat structure"""
    
    def __init__(self, r2: R2Uploader):
        self.r2 = r2
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.stats = {
            "segments_uploaded": 0,
            "segments_failed": 0
        }
        self.lock = Lock()
    
    def download_episode(self, hls_url: str, folder_prefix: str, episode_num: int) -> dict:
        """
        Download and upload an episode's HLS stream
        Uses NESTED structure: ep_001/index.m3u8, ep_001/segment_0000.ts
        """
        result = {
            "success": False,
            "episode_num": episode_num,
            "segments": 0,
            "duration": 0
        }
        
        try:
            # Get master playlist
            resp = self.session.get(hls_url, timeout=30)
            if resp.status_code != 200:
                logger.error(f"Failed to get playlist: {hls_url}")
                return result
            
            playlist_content = resp.text
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            
            # Episode subfolder: ep_001/, ep_002/, etc.
            ep_str = f"{episode_num:03d}"
            ep_folder = f"{folder_prefix}ep_{ep_str}/"
            
            # Parse and download segments with NESTED naming
            new_playlist_lines = []
            segment_count = 0
            
            for line in playlist_content.split('\n'):
                line = line.strip()
                if not line:
                    new_playlist_lines.append("")
                    continue
                
                if line.startswith('#'):
                    new_playlist_lines.append(line)
                    # Extract duration for stats
                    if line.startswith('#EXTINF:'):
                        try:
                            dur = float(line.split(':')[1].split(',')[0])
                            result["duration"] += dur
                        except:
                            pass
                    continue
                
                # This is a segment URL
                if line.endswith('.ts') or '.ts?' in line:
                    # NESTED naming: segment_0000.ts, segment_0001.ts, etc.
                    segment_name = f"segment_{segment_count:04d}.ts"
                    segment_key = f"{ep_folder}{segment_name}"
                    
                    # Get full URL
                    if line.startswith('http'):
                        segment_url = line
                    else:
                        segment_url = urljoin(base_url, line)
                    
                    # Download and upload segment
                    try:
                        seg_resp = self.session.get(segment_url, timeout=60)
                        if seg_resp.status_code == 200:
                            if self.r2.upload_bytes(seg_resp.content, segment_key, "video/MP2T"):
                                with self.lock:
                                    self.stats["segments_uploaded"] += 1
                            else:
                                with self.lock:
                                    self.stats["segments_failed"] += 1
                        new_playlist_lines.append(segment_name)
                        segment_count += 1
                    except Exception as e:
                        logger.error(f"Segment download failed: {e}")
                        new_playlist_lines.append(segment_name)
                        segment_count += 1
                        with self.lock:
                            self.stats["segments_failed"] += 1
                else:
                    new_playlist_lines.append(line)
            
            # Upload modified playlist with NESTED naming: ep_001/index.m3u8
            new_playlist = '\n'.join(new_playlist_lines)
            playlist_key = f"{ep_folder}index.m3u8"
            self.r2.upload_bytes(new_playlist.encode(), playlist_key, "application/x-mpegURL")
            
            result["success"] = True
            result["segments"] = segment_count
            logger.info(f"  ✓ Episode {episode_num}: {segment_count} segments in ep_{episode_num:03d}/")
            return result
            
        except Exception as e:
            logger.error(f"Episode {episode_num} failed: {e}")
            return result


# ============================================================================
# BATCH SCRAPER WITH SUPABASE
# ============================================================================

class BatchScraperSupabase:
    """Main scraper using JSON data with Supabase integration"""
    
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.r2 = R2Uploader()
        self.hls = HLSDownloader(self.r2)
        self.db = SupabaseClient()
        self.session = requests.Session()
        
        # FlickReels API session
        self.api_session = requests.Session()
        self.api_session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
        self.last_api_request = 0
        
        self.stats = {
            "dramas_done": 0,
            "dramas_skipped": 0,
            "dramas_failed": 0,
            "episodes_done": 0
        }
    
    def fetch_fresh_episodes(self, drama_id: str) -> list:
        """Fetch fresh episode list with valid HLS URLs from FlickReels API"""
        try:
            # Rate limit (100ms between requests)
            now = time.time()
            if now - self.last_api_request < 0.1:
                time.sleep(0.1)
            self.last_api_request = time.time()
            
            # Build request
            body = {**FLICKREELS_BODY, "playlet_id": drama_id}
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            sign = generate_sign(body, timestamp, nonce)
            
            headers = {
                "token": FLICKREELS_CONFIG["token"],
                "sign": sign,
                "timestamp": timestamp,
                "nonce": nonce
            }
            
            url = f"{FLICKREELS_CONFIG['base_url']}/app/playlet/chapterList"
            response = self.api_session.post(url, json=body, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return []
            
            result = response.json()
            if result.get("status_code") != 1:
                logger.error(f"API returned error: {result.get('message', 'Unknown')}")
                return []
            
            data = result.get("data", {})
            chapters = data.get("list", [])
            
            # Convert to our episode format
            episodes = []
            for ch in chapters:
                episodes.append({
                    "num": ch.get("chapter_num"),
                    "title": ch.get("chapter_title"),
                    "hls_url": ch.get("hls_url"),
                    "duration": ch.get("duration"),
                    "is_vip": ch.get("is_vip_episode", 0)
                })
            
            logger.info(f"  Fetched {len(episodes)} fresh episodes from API")
            return episodes
            
        except Exception as e:
            logger.error(f"fetch_fresh_episodes failed: {e}")
            return []
    
    def load_dramas(self) -> list:
        """Load dramas from JSON file (list format from discovery)"""
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Handle both list and dict format
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Convert dict to list
            return [{"id": k, **v} for k, v in data.items()]
        return []
    
    def get_existing_drama_ids(self) -> set:
        """Get drama IDs already in R2"""
        existing = set()
        folders = self.r2.list_folders("flickreels/")
        for folder in folders:
            # Extract ID from folder name like "Title (1234)"
            match = re.search(r'\((\d+)\)$', folder)
            if match:
                existing.add(match.group(1))
        return existing
    
    def download_cover(self, cover_url: str, folder_prefix: str) -> bool:
        """Download and upload cover image"""
        try:
            if not cover_url:
                return False
            resp = self.session.get(cover_url, timeout=30)
            if resp.status_code == 200:
                key = f"{folder_prefix}cover.jpg"
                return self.r2.upload_bytes(resp.content, key, "image/jpeg")
        except Exception as e:
            logger.error(f"Cover download failed: {e}")
        return False
    
    def scrape_drama(self, drama_data: dict) -> bool:
        """Scrape a single drama and insert to Supabase"""
        drama_id = str(drama_data.get('id', ''))
        title = drama_data.get('title', f'Drama {drama_id}')
        episodes = drama_data.get('episodes', [])
        cover_url = drama_data.get('cover', drama_data.get('cover_url', ''))
        total_episodes = drama_data.get('total_episodes', len(episodes))
        
        # Clean title for folder name
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
        folder_name = f"{safe_title} ({drama_id})"
        folder_prefix = f"flickreels/{folder_name}/"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Drama: {title}")
        logger.info(f"ID: {drama_id}, Episodes: {len(episodes)}")
        logger.info(f"Folder: {folder_name}")
        logger.info(f"{'='*60}")
        
        # Check if already complete in R2
        status_key = f"{folder_prefix}complete.json"
        if self.r2.file_exists(status_key):
            logger.info(f"  Already in R2, checking Supabase...")
            if not self.db.drama_exists(drama_id):
                # Need to insert to Supabase
                self._insert_to_supabase(drama_id, title, folder_name, cover_url, total_episodes, drama_data)
            self.stats["dramas_skipped"] += 1
            return True
        
        # Download cover
        logger.info("  Downloading cover...")
        self.download_cover(cover_url, folder_prefix)
        
        # Upload metadata to R2
        metadata = {
            "playlet_id": drama_id,
            "title": title,
            "cover_url": cover_url,
            "total_episodes": len(episodes),
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
        self.r2.upload_bytes(
            json.dumps(metadata, indent=2, ensure_ascii=False).encode(),
            f"{folder_prefix}metadata.json",
            "application/json"
        )
        
        # FETCH FRESH EPISODE DATA from FlickReels API
        # The HLS URLs in JSON are expired, need fresh ones
        logger.info(f"  Fetching fresh episode URLs from API...")
        fresh_episodes = self.fetch_fresh_episodes(drama_id)
        
        if fresh_episodes:
            episodes = fresh_episodes
        else:
            logger.warning(f"  Could not fetch fresh episodes, using stale URLs (may fail)")
        
        # Download episodes in parallel (12 at a time)
        logger.info(f"  Downloading {len(episodes)} episodes (12 parallel)...")
        
        episode_results = []
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = {}
            for ep in episodes:
                ep_num = ep.get('num', 0)
                hls_url = ep.get('hls_url', '')
                if hls_url and ep_num > 0:
                    future = executor.submit(
                        self.hls.download_episode,
                        hls_url,
                        folder_prefix,
                        ep_num
                    )
                    futures[future] = ep_num
            
            for future in as_completed(futures):
                ep_num = futures[future]
                try:
                    result = future.result()
                    if result["success"]:
                        self.stats["episodes_done"] += 1
                        episode_results.append(result)
                except Exception as e:
                    logger.error(f"  Episode {ep_num} error: {e}")
        
        # Mark complete in R2
        complete_data = {
            "status": "complete",
            "episodes": len(episodes),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        self.r2.upload_bytes(
            json.dumps(complete_data).encode(),
            status_key,
            "application/json"
        )
        
        # Insert to Supabase (as draft - is_published=false)
        self._insert_to_supabase(drama_id, title, folder_name, cover_url, total_episodes, drama_data)
        
        self.stats["dramas_done"] += 1
        logger.info(f"  ✓ Drama complete!")
        return True
    
    def _insert_to_supabase(self, drama_id: str, title: str, folder_name: str, 
                            cover_url: str, total_episodes: int, source_data: dict):
        """Insert drama to Supabase as draft"""
        if self.db.drama_exists(drama_id):
            logger.info(f"  Already in Supabase, skipping insert")
            return
        
        # Build R2 URLs
        r2_cover = f"/api/stream/flickreels/{folder_name}/cover.jpg"
        
        drama_record = {
            "title": title,
            "synopsis": "",  # Can be filled later
            "thumbnail_url": r2_cover,
            "total_episodes": total_episodes,
            "is_published": False,  # Draft - requires admin approval
            "flickreels_id": drama_id,
            "r2_folder": folder_name,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source_data": source_data
        }
        
        self.db.insert_drama(drama_record)
    
    def run(self, target_count: int = 428, start_from: int = 0):
        """Run the batch scraper"""
        logger.info("="*60)
        logger.info("Batch Scraper with Supabase Integration")
        logger.info(f"Target: {target_count} dramas")
        logger.info("="*60)
        
        # Load dramas from JSON
        all_dramas = self.load_dramas()
        logger.info(f"Total dramas in JSON: {len(all_dramas)}")
        
        # Get existing dramas in R2
        existing_ids = self.get_existing_drama_ids()
        logger.info(f"Existing dramas in R2: {len(existing_ids)}")
        
        # Filter and prepare
        to_scrape = []
        for drama in all_dramas:
            drama_id = str(drama.get('id', ''))
            if drama_id and drama_id not in existing_ids:
                to_scrape.append(drama)
        
        logger.info(f"New dramas to scrape: {len(to_scrape)}")
        
        if not to_scrape:
            logger.info("No new dramas found!")
            return
        
        # Limit to target count
        if start_from > 0:
            to_scrape = to_scrape[start_from:]
        if len(to_scrape) > target_count:
            to_scrape = to_scrape[:target_count]
        
        logger.info(f"Will scrape {len(to_scrape)} dramas")
        
        # Scrape each drama
        start_time = time.time()
        for i, drama in enumerate(to_scrape, 1):
            drama_id = str(drama.get('id', ''))
            logger.info(f"\n[{i}/{len(to_scrape)}] Processing drama {drama_id}")
            
            try:
                self.scrape_drama(drama)
            except Exception as e:
                logger.error(f"Drama {drama_id} failed: {e}")
                self.stats["dramas_failed"] += 1
            
            # Progress log
            elapsed = time.time() - start_time
            rate = i / elapsed * 60 if elapsed > 0 else 0
            remaining = (len(to_scrape) - i) / rate if rate > 0 else 0
            
            logger.info(f"\nPROGRESS: {i}/{len(to_scrape)} dramas, "
                       f"{self.stats['episodes_done']} episodes, "
                       f"{self.hls.stats['segments_uploaded']} segments, "
                       f"Rate: {rate:.1f}/min, ETA: {remaining:.0f} min")
            
            # Save progress periodically
            if i % 10 == 0:
                self._save_progress(i, len(to_scrape))
        
        # Final stats
        elapsed = time.time() - start_time
        logger.info("\n" + "="*60)
        logger.info("BATCH SCRAPE COMPLETE!")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info(f"Dramas: {self.stats['dramas_done']} done, "
                   f"{self.stats['dramas_skipped']} skipped, "
                   f"{self.stats['dramas_failed']} failed")
        logger.info(f"Episodes: {self.stats['episodes_done']}")
        logger.info(f"Segments: {self.hls.stats['segments_uploaded']} uploaded, "
                   f"{self.hls.stats['segments_failed']} failed")
        logger.info("="*60)
    
    def _save_progress(self, current: int, total: int):
        """Save progress to file"""
        progress = {
            "current": current,
            "total": total,
            "stats": self.stats,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open("scrape_progress.json", "w") as f:
            json.dump(progress, f, indent=2)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Batch scraper with Supabase integration")
    parser.add_argument("--json", default="new_dramas_for_app.json", help="Path to dramas JSON file")
    parser.add_argument("--target", type=int, default=115, help="Target number of dramas")
    parser.add_argument("--start", type=int, default=0, help="Start from drama index")
    parser.add_argument("--test", action="store_true", help="Test mode - scrape 1 drama only")
    parser.add_argument("--fresh", action="store_true", help="Fresh start - clear progress files")
    args = parser.parse_args()
    
    # Fresh start - clear progress files
    if args.fresh:
        for pf in ["scraped_ids.txt", "scrape_progress.json"]:
            if os.path.exists(pf):
                os.remove(pf)
                logger.info(f"Cleared progress file: {pf}")
    
    # Handle relative path
    json_path = args.json
    if not os.path.isabs(json_path):
        json_path = os.path.join(os.path.dirname(__file__), json_path)
    
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        sys.exit(1)
    
    logger.info(f"Using JSON file: {json_path}")
    
    target = 1 if args.test else args.target
    
    scraper = BatchScraperSupabase(json_path)
    scraper.run(target_count=target, start_from=args.start)


if __name__ == "__main__":
    main()
