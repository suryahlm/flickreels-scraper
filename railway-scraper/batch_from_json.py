#!/usr/bin/env python3
"""
Batch Scraper from dramas_indonesia.json
=========================================
Scrapes Indonesian dramas using the pre-captured API data file.
This is much faster since we already have all drama data!

Features:
- Uses dramas_indonesia.json as data source (no API discovery needed)
- Downloads HLS streams and uploads to R2
- 12 parallel episodes per drama
- Skips already-completed dramas
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import re
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

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# R2 Configuration
R2_CONFIG = {
    "account_id": os.environ.get("R2_ACCOUNT_ID", "0bff99fdd0a5e3eb7b2c3e7ab2b16c6a"),
    "access_key": os.environ.get("R2_ACCESS_KEY_ID", "c1c74baa55bd8ceee9a8ed7a17a10c49"),
    "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY", "a444da6d9d68e97b69ac1ea65ca0f70af5cb7f95eab2ec94eca9c63f8b39b87b"),
    "bucket": os.environ.get("R2_BUCKET_NAME", "asiandrama"),
    "public_url": "https://pub-6715a9ccd86747f2b0013087e22a7479.r2.dev"
}


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
    
    def upload_bytes(self, data: bytes, key: str, content_type: str = "application/octet-stream"):
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


class HLSDownloader:
    """Downloads HLS streams and uploads to R2"""
    
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
    
    def download_episode(self, hls_url: str, folder_prefix: str, episode_num: int) -> bool:
        """Download and upload an episode's HLS stream"""
        try:
            # Get master playlist
            resp = self.session.get(hls_url, timeout=30)
            if resp.status_code != 200:
                logger.error(f"Failed to get playlist: {hls_url}")
                return False
            
            playlist_content = resp.text
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            
            # Parse and download segments
            new_playlist_lines = []
            segment_count = 0
            
            for line in playlist_content.split('\n'):
                line = line.strip()
                if not line:
                    new_playlist_lines.append("")
                    continue
                
                if line.startswith('#'):
                    new_playlist_lines.append(line)
                    continue
                
                # This is a segment URL
                if line.endswith('.ts') or '.ts?' in line:
                    segment_count += 1
                    segment_name = f"segment_{segment_count:04d}.ts"
                    segment_key = f"{folder_prefix}ep{episode_num:02d}/{segment_name}"
                    
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
                    except Exception as e:
                        logger.error(f"Segment download failed: {e}")
                        new_playlist_lines.append(segment_name)  # Still add to playlist
                        with self.lock:
                            self.stats["segments_failed"] += 1
                else:
                    new_playlist_lines.append(line)
            
            # Upload modified playlist
            new_playlist = '\n'.join(new_playlist_lines)
            playlist_key = f"{folder_prefix}ep{episode_num:02d}.m3u8"
            self.r2.upload_bytes(new_playlist.encode(), playlist_key, "application/x-mpegURL")
            
            logger.info(f"  ✓ Episode {episode_num}: {segment_count} segments")
            return True
            
        except Exception as e:
            logger.error(f"Episode {episode_num} failed: {e}")
            return False


class BatchScraperFromJSON:
    """Main scraper using pre-captured JSON data"""
    
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.r2 = R2Uploader()
        self.hls = HLSDownloader(self.r2)
        self.session = requests.Session()
        self.stats = {
            "dramas_done": 0,
            "dramas_skipped": 0,
            "episodes_done": 0
        }
    
    def load_dramas(self) -> dict:
        """Load dramas from JSON file"""
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
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
                # Determine extension
                ext = "jpg"
                if "png" in cover_url.lower():
                    ext = "png"
                key = f"{folder_prefix}cover.{ext}"
                return self.r2.upload_bytes(resp.content, key, f"image/{ext}")
        except Exception as e:
            logger.error(f"Cover download failed: {e}")
        return False
    
    def scrape_drama(self, drama_id: str, drama_data: dict) -> bool:
        """Scrape a single drama"""
        title = drama_data.get('title', f'Drama {drama_id}')
        episodes = drama_data.get('episodes', [])
        cover_url = drama_data.get('cover_url', '')
        
        # Clean title for folder name
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
        folder_name = f"{safe_title} ({drama_id})"
        folder_prefix = f"flickreels/{folder_name}/"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Drama: {title}")
        logger.info(f"ID: {drama_id}, Episodes: {len(episodes)}")
        logger.info(f"Folder: {folder_name}")
        logger.info(f"{'='*60}")
        
        # Check if already complete
        status_key = f"{folder_prefix}complete.json"
        if self.r2.file_exists(status_key):
            logger.info(f"  Already complete, skipping...")
            self.stats["dramas_skipped"] += 1
            return True
        
        # Download cover
        logger.info("  Downloading cover...")
        self.download_cover(cover_url, folder_prefix)
        
        # Upload metadata
        metadata = {
            "playlet_id": drama_id,
            "title": title,
            "description": drama_data.get('description', ''),
            "language": drama_data.get('language', 'id'),
            "cover_url": cover_url,
            "total_episodes": len(episodes),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.r2.upload_bytes(
            json.dumps(metadata, indent=2, ensure_ascii=False).encode(),
            f"{folder_prefix}metadata.json",
            "application/json"
        )
        
        # Download episodes in parallel (12 at a time)
        logger.info(f"  Downloading {len(episodes)} episodes (12 parallel)...")
        
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = {}
            for i, ep in enumerate(episodes, 1):
                hls_url = ep.get('hls_url', '')
                if hls_url:
                    future = executor.submit(
                        self.hls.download_episode,
                        hls_url,
                        folder_prefix,
                        i
                    )
                    futures[future] = i
            
            for future in as_completed(futures):
                ep_num = futures[future]
                try:
                    if future.result():
                        self.stats["episodes_done"] += 1
                except Exception as e:
                    logger.error(f"  Episode {ep_num} error: {e}")
        
        # Mark complete
        complete_data = {
            "status": "complete",
            "episodes": len(episodes),
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.r2.upload_bytes(
            json.dumps(complete_data).encode(),
            status_key,
            "application/json"
        )
        
        self.stats["dramas_done"] += 1
        logger.info(f"  ✓ Drama complete!")
        return True
    
    def run(self, target_count: int = 300, start_from: int = 0):
        """Run the batch scraper"""
        logger.info("="*60)
        logger.info("Batch Scraper from JSON")
        logger.info(f"Target: {target_count} dramas")
        logger.info("="*60)
        
        # Load dramas from JSON
        all_dramas = self.load_dramas()
        logger.info(f"Total dramas in JSON: {len(all_dramas)}")
        
        # Get existing dramas in R2
        existing_ids = self.get_existing_drama_ids()
        logger.info(f"Existing dramas in R2: {len(existing_ids)}")
        
        # Filter out existing dramas
        to_scrape = []
        for drama_id, drama_data in all_dramas.items():
            if drama_id not in existing_ids:
                to_scrape.append((drama_id, drama_data))
        
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
        for i, (drama_id, drama_data) in enumerate(to_scrape, 1):
            logger.info(f"\n[{i}/{len(to_scrape)}] Processing drama {drama_id}")
            
            try:
                self.scrape_drama(drama_id, drama_data)
            except Exception as e:
                logger.error(f"Drama {drama_id} failed: {e}")
            
            # Progress log
            elapsed = time.time() - start_time
            rate = i / elapsed * 60 if elapsed > 0 else 0
            remaining = (len(to_scrape) - i) / rate if rate > 0 else 0
            
            logger.info(f"\nPROGRESS: {i}/{len(to_scrape)} dramas, "
                       f"{self.stats['episodes_done']} episodes, "
                       f"{self.hls.stats['segments_uploaded']} segments, "
                       f"Rate: {rate:.1f}/min, ETA: {remaining:.0f} min")
        
        # Final stats
        elapsed = time.time() - start_time
        logger.info("\n" + "="*60)
        logger.info("BATCH SCRAPE COMPLETE!")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info(f"Dramas: {self.stats['dramas_done']} done, {self.stats['dramas_skipped']} skipped")
        logger.info(f"Episodes: {self.stats['episodes_done']}")
        logger.info(f"Segments: {self.hls.stats['segments_uploaded']} uploaded, {self.hls.stats['segments_failed']} failed")
        logger.info("="*60)


def main():
    parser = argparse.ArgumentParser(description="Batch scraper from JSON file")
    parser.add_argument("--json", default="../dramas_indonesia.json", help="Path to dramas JSON file")
    parser.add_argument("--target", type=int, default=300, help="Target number of dramas")
    parser.add_argument("--start", type=int, default=0, help="Start from drama index")
    parser.add_argument("--list", action="store_true", help="Just list dramas in JSON")
    args = parser.parse_args()
    
    # Handle relative path
    json_path = args.json
    if not os.path.isabs(json_path):
        json_path = os.path.join(os.path.dirname(__file__), json_path)
    
    if not os.path.exists(json_path):
        # Try parent directory
        json_path = os.path.join(os.path.dirname(__file__), "..", "dramas_indonesia.json")
    
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        sys.exit(1)
    
    logger.info(f"Using JSON file: {json_path}")
    
    if args.list:
        with open(json_path, 'r', encoding='utf-8') as f:
            dramas = json.load(f)
        print(f"\nTotal dramas: {len(dramas)}\n")
        for i, (drama_id, data) in enumerate(dramas.items(), 1):
            print(f"{i:3}. [{drama_id}] {data.get('title', 'Unknown')} ({len(data.get('episodes', []))} eps)")
        return
    
    scraper = BatchScraperFromJSON(json_path)
    scraper.run(target_count=args.target, start_from=args.start)


if __name__ == "__main__":
    main()
