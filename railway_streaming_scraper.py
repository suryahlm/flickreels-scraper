"""
FlickReels → R2 Streaming Scraper
==================================

STREAMING UPLOAD - NO LOCAL STORAGE!
- Download dari FlickReels API
- Upload langsung ke R2
- Never touch disk (all in memory)
- Designed untuk Railway deployment

Perfect for:
- Limited disk space
- Background processing
- Laptop bisa dimatikan

Usage:
    python railway_streaming_scraper.py --drama=2858 --episodes=5
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
from io import BytesIO

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

DEFAULT_BODY_PARAMS = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID",
    "language_id": "6"  # Indonesian
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API SIGNING
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
    
    def _request(self, endpoint: str, extra_body: dict = None) -> dict:
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
        
        try:
            response = self.session.post(url, json=body, headers=headers, timeout=30)
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"status_code": -1, "msg": str(e)}
    
    def get_episodes(self, playlet_id: str) -> List[dict]:
        """Get episode list for drama"""
        result = self._request("/app/playlet/chapterList", {"playlet_id": playlet_id})
        
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
    
    def get_stream_url(self, playlet_id: str, chapter_id: str) -> Optional[dict]:
        """Get fresh HLS URL and tags for episode"""
        result = self._request("/app/playlet/play", {
            "playlet_id": playlet_id,
            "chapter_id": chapter_id
        })
        
        if result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        hls_url = data.get("hls_url") or data.get("hls")
        
        if not hls_url:
            return None
        
        # Extract tags/genres
        tags = [t.get("tag_name") for t in data.get("tag_list", [])]
        
        return {
            "hls_url": hls_url,
            "tags": tags,
            "duration": data.get("total_duration")
        }

# ============================================================================
# R2 STREAMING UPLOADER
# ============================================================================

class R2StreamUploader:
    """Upload directly to R2 without touching local disk"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG["endpoint_url"],
            aws_access_key_id=R2_CONFIG["access_key_id"],
            aws_secret_access_key=R2_CONFIG["secret_access_key"],
            config=Config(signature_version='s3v4')
        )
        self.bucket = R2_CONFIG["bucket_name"]
    
    def upload_stream(self, url: str, r2_key: str, content_type: str = None) -> bool:
        """
        Download from URL and stream directly to R2 (no disk write)
        
        Args:
            url: Source URL to download from
            r2_key: Destination path in R2 (e.g. "flickreels/2858/ep_001.m3u8")
            content_type: MIME type
        
        Returns:
            True if successful
        """
        try:
            # Stream download (don't load entire file into memory)
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Upload directly from stream
            self.client.upload_fileobj(
                response.raw,
                self.bucket,
                r2_key,
                ExtraArgs={'ContentType': content_type} if content_type else {}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Stream upload failed for {r2_key}: {e}")
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
# STREAMING SCRAPER
# ============================================================================

class StreamingScraper:
    """Main scraper with streaming upload (no local storage)"""
    
    def __init__(self):
        self.api = FlickReelsAPI()
        self.uploader = R2StreamUploader()
        self.stats = {
            "episodes_processed": 0,
            "segments_uploaded": 0,
            "bytes_uploaded": 0,
            "errors": 0
        }
    
    def parse_m3u8(self, content: str, base_url: str) -> List[str]:
        """Parse m3u8 and extract segment URLs"""
        segments = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            # This is a segment URL
            if line.endswith('.ts') or '.ts?' in line:
                if not line.startswith('http'):
                    # Relative URL
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
                # Replace with R2 path (relative to m3u8 location)
                new_lines.append(f"{episode_prefix}_{segment_index:04d}.ts")
                segment_index += 1
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def scrape_episode(
        self, 
        drama_id: str,
        episode_num: int,
        chapter_id: str
    ) -> bool:
        """
        Scrape single episode with STREAMING upload
        
        Flow:
        1. Get fresh HLS URL
        2. Download m3u8 to memory
        3. Parse segment URLs
        4. For each segment:
           - Stream download from CDN
           - Stream upload to R2
           - Discard from memory
        5. Upload rewritten m3u8
        
        NO DISK WRITES!
        """
        logger.info(f"[EP {episode_num}] Getting stream URL...")
        
        # 1. Get fresh HLS URL and tags
        stream_data = self.api.get_stream_url(drama_id, chapter_id)
        if not stream_data:
            logger.error(f"[EP {episode_num}] Failed to get HLS URL")
            self.stats["errors"] += 1
            return False
        
        hls_url = stream_data["hls_url"]
        tags = stream_data.get("tags", [])
        
        # 2. Download m3u8 manifest (small file, keep in memory)
        logger.info(f"[EP {episode_num}] Downloading manifest...")
        try:
            response = requests.get(hls_url, timeout=30)
            response.raise_for_status()
            m3u8_content = response.text
        except Exception as e:
            logger.error(f"[EP {episode_num}] Failed to download manifest: {e}")
            self.stats["errors"] += 1
            return False
        
        # 3. Parse segment URLs
        base_url = hls_url.rsplit('/', 1)[0] + '/'
        segments = self.parse_m3u8(m3u8_content, base_url)
        
        if not segments:
            logger.warning(f"[EP {episode_num}] No segments found")
            return False
        
        logger.info(f"[EP {episode_num}] Found {len(segments)} segments")
        
        # 4. Stream upload each segment (NO LOCAL STORAGE!)
        episode_prefix = f"ep_{episode_num:03d}"
        r2_episode_dir = f"flickreels/{drama_id}/episodes"
        
        for i, segment_url in enumerate(segments):
            logger.info(f"[EP {episode_num}] Segment {i+1}/{len(segments)}")
            
            r2_key = f"{r2_episode_dir}/{episode_prefix}_{i:04d}.ts"
            
            if self.uploader.upload_stream(segment_url, r2_key, "video/mp2t"):
                self.stats["segments_uploaded"] += 1
            else:
                logger.error(f"[EP {episode_num}] Failed segment {i}")
                self.stats["errors"] += 1
                return False
        
        # 5. Upload rewritten m3u8
        new_m3u8 = self.rewrite_m3u8(m3u8_content, episode_prefix)
        r2_manifest_key = f"{r2_episode_dir}/{episode_prefix}.m3u8"
        
        if self.uploader.upload_bytes(
            new_m3u8.encode('utf-8'),
            r2_manifest_key,
            "application/vnd.apple.mpegurl"
        ):
            logger.info(f"[EP {episode_num}] ✅ Complete!")
            self.stats["episodes_processed"] += 1
            return True
        else:
            logger.error(f"[EP {episode_num}] Failed to upload manifest")
            return False
    
    def scrape_drama(self, drama_id: str, max_episodes: int = None):
        """Scrape complete drama"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting scrape: Drama {drama_id}")
        logger.info(f"{'='*60}\n")
        
        # Get episodes
        episodes = self.api.get_episodes(drama_id)
        
        if not episodes:
            logger.error("No episodes found")
            return
        
        if max_episodes:
            episodes = episodes[:max_episodes]
        
        logger.info(f"Total episodes to scrape: {len(episodes)}")
        
        # Process each episode
        start_time = time.time()
        all_tags = []  # NEW: collect tags from all episodes
        
        for i, episode in enumerate(episodes):
            ep_num = i + 1
            chapter_id = episode.get("chapter_id")
            
            if not chapter_id:
                logger.warning(f"Skipping EP {ep_num} - no chapter_id")
                continue
            
            logger.info(f"\n[{ep_num}/{len(episodes)}] Processing...")
            
            # Get stream data for tags (do this BEFORE downloading if we just need tags)
            stream_data = self.api.get_stream_url(drama_id, chapter_id)
            if stream_data and stream_data.get("tags"):
                all_tags.extend(stream_data["tags"])
            
            success = self.scrape_episode(drama_id, ep_num, chapter_id)
            
            if not success:
                logger.warning(f"EP {ep_num} failed, continuing...")
            
            # Rate limiting
            time.sleep(0.5)
        
        # Get unique tags/genres
        unique_tags = list(set(all_tags))
        logger.info(f"\nGenres/Tags found: {', '.join(unique_tags)}")
        
        # Upload metadata with tags
        metadata = {
            "playlet_id": drama_id,
            "total_episodes": len(episodes),
            "genres": unique_tags,  # NEW: store genres
            "scraped_at": datetime.now().isoformat(),
            "episodes": episodes
        }
        
        self.uploader.upload_json(metadata, f"flickreels/{drama_id}/metadata.json")
        
        # Mark complete
        self.uploader.upload_json(
            {"completed_at": datetime.now().isoformat()},
            f"flickreels/{drama_id}/complete.json"
        )
        
        # Print stats
        elapsed = time.time() - start_time
        logger.info(f"\n{'='*60}")
        logger.info("SCRAPE COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Episodes processed: {self.stats['episodes_processed']}")
        logger.info(f"Segments uploaded: {self.stats['segments_uploaded']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Time: {elapsed/60:.1f} minutes")
        logger.info(f"{'='*60}\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FlickReels Streaming Scraper")
    parser.add_argument("--drama", type=str, required=True, help="Drama ID to scrape")
    parser.add_argument("--episodes", type=int, help="Max episodes to scrape (default: all)")
    
    args = parser.parse_args()
    
    scraper = StreamingScraper()
    scraper.scrape_drama(args.drama, args.episodes)
