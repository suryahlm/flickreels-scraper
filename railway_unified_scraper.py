"""
FlickReels Unified Railway Scraper
===================================

FULL PIPELINE: Metadata → Video Download → R2 Upload

This is the ULTIMATE scraper that combines:
1. railway_scraper.py (metadata scraping)
2. download_videos.py (HLS video download)  
3. upload_to_r2.py (R2 cloud upload)

Into ONE automated Railway worker.

Usage:
    # Full pipeline (metadata + video + R2)
    python railway_unified_scraper.py --mode=full --limit=5
    
    # Metadata only
    python railway_unified_scraper.py --mode=metadata --scan=100
    
    # Video download + upload only (requires existing metadata)
    python railway_unified_scraper.py --mode=upload --drama-ids=2858,533
    
    # Resume upload for already downloaded videos
    python railway_unified_scraper.py --mode=resume

Environment Variables:
    FLICKREELS_TOKEN
    R2_ACCOUNT_ID
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET_NAME (default: asiandrama-cdn)
"""

import argparse
import hashlib
import hmac
import json
import os
import random
import string
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

# R2 dependencies
try:
    import boto3
    from botocore.config import Config
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("[WARN] boto3 not installed - R2 upload will be disabled")

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent

# FlickReels API
FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.getenv("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0",
    "user_agent": "MyUserAgent"
}

# R2 Configuration
R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "asiandrama-cdn"),
    "endpoint_url": None  # Will be constructed from account_id
}

# Default device params (Indonesian partition)
DEFAULT_DEVICE_PARAMS = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID",
    "language_id": "6"  # INDONESIAN
}

# Content types
CONTENT_TYPES = {
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".json": "application/json",
    ".jpg": "image/jpeg",
}

# Scraping settings
SETTINGS = {
    "request_delay": 0.3,
    "max_retries": 3,
    "timeout": 30,
    "r2_prefix": "flickreels"
}

# ============================================================================
# UTILS
# ============================================================================

def generate_nonce(length: int = 32) -> str:
    """Generate random nonce for API signing."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def method_d(body_json: str) -> str:
    """FlickReels body normalization for signing."""
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

def generate_sign(body: Dict, timestamp: str, nonce: str) -> str:
    """Generate HMAC-SHA256 signature for FlickReels API."""
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

def sanitize_filename(name: str) -> str:
    """Sanitize filename for filesystem compatibility."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.strip().strip('.')
    if len(name) > 100:
        name = name[:100]
    return name

# ============================================================================
# FLICKREELS API CLIENT
# ============================================================================

class FlickReelsAPI:
    """FlickReels API client with auto-signing."""
    
    def __init__(self):
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
            "token": FLICKREELS_CONFIG["token"],
            "sign": sign,
            "timestamp": timestamp,
            "nonce": nonce
        }
        
        url = f"{FLICKREELS_CONFIG['base_url']}{endpoint}"
        
        for attempt in range(SETTINGS["max_retries"]):
            try:
                response = self.session.post(
                    url, 
                    json=body, 
                    headers=headers,
                    timeout=SETTINGS["timeout"]
                )
                return response.json()
            except Exception as e:
                if attempt < SETTINGS["max_retries"] - 1:
                    time.sleep(1)
                else:
                    print(f"[ERROR] Request failed: {e}")
                    return {"status_code": -1, "msg": str(e)}
        
        return {"status_code": -1}
    
    def get_dramas_from_navigation(self, nav_id: int) -> List[Dict]:
        """Get dramas from navigation category."""
        result = self._request("/app/playlet/navigationColumn", {
            "navigation_id": nav_id,
            "page": 1,
            "page_size": 100
        })
        
        dramas = []
        if result.get("status_code") == 1:
            data = result.get("data", [])
            for col in data if isinstance(data, list) else []:
                for drama in col.get("list", []):
                    dramas.append({
                        "playlet_id": str(drama.get("playlet_id")),
                        "title": drama.get("title"),
                        "cover_url": drama.get("cover_url") or drama.get("cover"),
                        "chapter_total": drama.get("chapter_total", 0)
                    })
        
        return dramas
    
    def get_episodes(self, playlet_id: str) -> List[dict]:
        """Get episode list for a drama."""
        result = self._request("/app/playlet/chapterList", {
            "playlet_id": playlet_id
        })
        
        if result.get("status_code") != 1:
            return []
        
        data = result.get("data", {})
        episode_list = data.get("list", []) if isinstance(data, dict) else []
        
        episodes = []
        for ep in episode_list:
            episodes.append({
                "chapter_id": ep.get("chapter_id"),
                "title": ep.get("title", f"EP.{ep.get('sort', 1)}"),
                "chapter_num": ep.get("sort", 1),
                "duration": ep.get("duration", 0),
                "is_free": ep.get("is_free", 0) == 1,
                "is_vip": ep.get("is_vip", 0) == 1
            })
        
        return episodes
    
    def get_stream_url(self, playlet_id: str, chapter_id: str) -> Optional[str]:
        """Get HLS stream URL for an episode."""
        result = self._request("/app/playlet/play", {
            "playlet_id": playlet_id,
            "chapter_id": chapter_id
        })
        
        if result.get("status_code") != 1:
            return None
        
        data = result.get("data", {})
        return data.get("hls_url") or data.get("hls")

# ============================================================================
# R2 STORAGE CLIENT  
# ============================================================================

class R2Storage:
    """Cloudflare R2 storage client."""
    
    def __init__(self):
        if not HAS_BOTO3:
            raise ImportError("boto3 is required. Install: pip install boto3")
        
        R2_CONFIG["endpoint_url"] = f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com"
        
        self.client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG["endpoint_url"],
            aws_access_key_id=R2_CONFIG["access_key_id"],
            aws_secret_access_key=R2_CONFIG["secret_access_key"],
            config=Config(signature_version='s3v4')
        )
        self.bucket = R2_CONFIG["bucket_name"]
        self.prefix = SETTINGS["r2_prefix"]
        
        print(f"[R2] Connected to bucket: {self.bucket}")
    
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
    
    def upload_file(self, local_path: Path, r2_path: str, content_type: str = None) -> bool:
        """Upload file to R2."""
        try:
            if not content_type:
                content_type = CONTENT_TYPES.get(local_path.suffix, "application/octet-stream")
            
            with open(local_path, 'rb') as f:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=self._key(r2_path),
                    Body=f,
                    ContentType=content_type,
                    CacheControl="public, max-age=31536000"
                )
            return True
        except Exception as e:
            print(f"    [ERROR] Upload failed {r2_path}: {e}")
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
            print(f"    [ERROR] JSON upload failed {path}: {e}")
            return False
    
    def upload_from_url(self, url: str, r2_path: str) -> bool:
        """Download from URL and upload to R2."""
        try:
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            self.client.put_object(
                Bucket=self.bucket,
                Key=self._key(r2_path),
                Body=response.content,
                ContentType=content_type
            )
            return True
        except Exception as e:
            print(f"    [ERROR] URL upload failed {r2_path}: {e}")
            return False

# ============================================================================
# HLS VIDEO DOWNLOADER
# ============================================================================

class HLSDownloader:
    """Download HLS video streams."""
    
    def __init__(self, output_dir: Path, api: FlickReelsAPI):
        self.output_dir = output_dir
        self.api = api
        self.session = requests.Session()
        self.stats = {"segments": 0, "episodes": 0, "errors": 0}
    
    def parse_m3u8(self, content: str, base_url: str) -> List[str]:
        """Parse M3U8 and extract segment URLs."""
        segments = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if line.endswith('.ts') or '.ts?' in line:
                if not line.startswith('http'):
                    segment_url = urljoin(base_url, line)
                else:
                    segment_url = line
                segments.append(segment_url)
        return segments
    
    def rewrite_m3u8(self, content: str, prefix: str) -> str:
        """Rewrite M3U8 to use local segment paths."""
        lines = content.strip().split('\n')
        new_lines = []
        segment_index = 0
        
        for line in lines:
            line = line.strip()
            if line.endswith('.ts') or '.ts?' in line:
                new_lines.append(f"{prefix}_{segment_index:04d}.ts")
                segment_index += 1
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def download_episode(self, drama_folder: str, ep_num: int, hls_url: str) -> bool:
        """Download complete episode (manifest + segments)."""
        episode_dir = self.output_dir / drama_folder
        episode_prefix = f"ep_{ep_num:03d}"
        manifest_path = episode_dir / f"{episode_prefix}.m3u8"
        
        # Skip if exists
        if manifest_path.exists():
            print(f"    [SKIP] Episode {ep_num} already downloaded")
            return True
        
        try:
            # Download manifest
            response = self.session.get(hls_url, timeout=SETTINGS["timeout"])
            response.raise_for_status()
            manifest_content = response.text
            
            # Parse segments
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            segments = self.parse_m3u8(manifest_content, base_url)
            
            if not segments:
                print(f"    [WARN] No segments found for EP {ep_num}")
                return False
            
            print(f"    Downloading {len(segments)} segments...")
            episode_dir.mkdir(parents=True, exist_ok=True)
            
            # Download segments
            for i, segment_url in enumerate(segments):
                segment_path = episode_dir / f"{episode_prefix}_{i:04d}.ts"
                
                # Download with retry
                for attempt in range(SETTINGS["max_retries"]):
                    try:
                        seg_response = self.session.get(segment_url, timeout=SETTINGS["timeout"])
                        seg_response.raise_for_status()
                        
                        with open(segment_path, 'wb') as f:
                            f.write(seg_response.content)
                        
                        self.stats["segments"] += 1
                        break
                    except Exception as e:
                        if attempt == SETTINGS["max_retries"] - 1:
                            print(f"      [ERROR] Segment {i} failed: {e}")
                            self.stats["errors"] += 1
                            return False
                        time.sleep(1)
                
                if (i + 1) % 10 == 0:
                    print(f"      Progress: {i + 1}/{len(segments)}")
            
            # Save rewritten manifest
            new_manifest = self.rewrite_m3u8(manifest_content, episode_prefix)
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(new_manifest)
            
            self.stats["episodes"] += 1
            return True
            
        except Exception as e:
            print(f"    [ERROR] Episode {ep_num} download failed: {e}")
            self.stats["errors"] += 1
            return False

# ============================================================================
# UNIFIED SCRAPER
# ============================================================================

class UnifiedScraper:
    """Unified scraper: Metadata → Download → R2 Upload."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.api = FlickReelsAPI()
        self.storage = R2Storage() if HAS_BOTO3 else None
        self.downloader = HLSDownloader(temp_dir, self.api)
        self.stats = {
            "dramas_processed": 0,
            "episodes_downloaded": 0,
            "files_uploaded": 0,
            "start_time": datetime.now()
        }
    
    def scrape_drama_full(self, drama_id: str, drama_info: dict = None) -> bool:
        """Full pipeline for single drama: metadata → download → upload."""
        
        # Get metadata if not provided
        if not drama_info:
            episodes = self.api.get_episodes(drama_id)
            drama_info = {
                "playlet_id": drama_id,
                "title": f"Drama {drama_id}",
                "episodes": episodes
            }
        
        title = drama_info.get("title", "Unknown")
        episodes = drama_info.get("episodes", [])
        
        if not episodes:
            print(f"  [SKIP] {title} - No episodes")
            return False
        
        print(f"\n[DRAMA] {title} (ID: {drama_id}) - {len(episodes)} episodes")
        
        # Create folder
        folder_name = sanitize_filename(f"{title} ({drama_id})")
        drama_dir = self.temp_dir / folder_name
        drama_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata locally
        metadata = {
            "id": drama_id,
            "title": title,
            "cover_url": drama_info.get("cover_url", ""),
            "chapter_total": len(episodes),
            "scraped_at": datetime.now().isoformat()
        }
        
        with open(drama_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Download cover
        cover_url = drama_info.get("cover_url")
        if cover_url:
            print(f"  [COVER] Downloading cover...")
            try:
                response = requests.get(cover_url, timeout=30)
                with open(drama_dir / "cover.jpg", 'wb') as f:
                    f.write(response.content)
            except Exception as e:
                print(f"    [WARN] Cover download failed: {e}")
        
        # Download episodes
        for i, episode in enumerate(episodes):
            ep_num = i + 1
            chapter_id = episode.get("chapter_id")
            
            if not chapter_id:
                continue
            
            print(f"  [EP {ep_num}/{len(episodes)}] Fetching stream URL...")
            
            # Get fresh HLS URL
            hls_url = self.api.get_stream_url(drama_id, chapter_id)
            
            if not hls_url:
                print(f"    [ERROR] Failed to get stream URL")
                continue
            
            # Download episode
            self.downloader.download_episode(folder_name, ep_num, hls_url)
            time.sleep(SETTINGS["request_delay"])
        
        # Upload to R2
        if self.storage:
            print(f"  [R2] Uploading {folder_name} to R2...")
            self._upload_drama_folder(drama_dir, folder_name)
        
        self.stats["dramas_processed"] += 1
        return True
    
    def _upload_drama_folder(self, local_dir: Path, folder_name: str) -> bool:
        """Upload entire drama folder to R2."""
        files = list(local_dir.glob("*"))
        uploaded = 0
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            r2_path = f"{folder_name}/{file_path.name}"
            
            # Skip if exists
            if self.storage.exists(r2_path):
                continue
            
            if self.storage.upload_file(file_path, r2_path):
                uploaded += 1
                self.stats["files_uploaded"] += 1
        
        print(f"    Uploaded {uploaded} files")
        return True
    
    def run_full_pipeline(self, nav_scan_range: int = 100, limit: int = None):
        """Run full pipeline: discover → scrape → download → upload."""
        
        print("="*60)
        print("FLICKREELS UNIFIED SCRAPER - FULL PIPELINE")
        print(f"Navigation Scan: 1-{nav_scan_range}")
        print(f"Limit: {limit if limit else 'None'}")
        print("="*60)
        
        # Discover dramas
        print("\n[DISCOVERY] Scanning navigation categories...")
        all_dramas = {}
        
        for nav_id in range(1, nav_scan_range + 1):
            dramas = self.api.get_dramas_from_navigation(nav_id)
            for d in dramas:
                pid = d["playlet_id"]
                if pid not in all_dramas:
                    all_dramas[pid] = d
            
            if nav_id % 20 == 0:
                print(f"  Progress: nav {nav_id}, found {len(all_dramas)} dramas")
            
            time.sleep(SETTINGS["request_delay"])
        
        print(f"\n[INFO] Found {len(all_dramas)} unique dramas")
        
        # Limit if specified
        if limit:
            drama_ids = list(all_dramas.keys())[:limit]
        else:
            drama_ids = list(all_dramas.keys())
        
        print(f"[INFO] Processing {len(drama_ids)} dramas\n")
        
        # Process each drama
        for drama_id in drama_ids:
            drama_info = all_dramas.get(drama_id, {})
            
            # Get full episode list
            episodes = self.api.get_episodes(drama_id)
            drama_info["episodes"] = episodes
            
            # Process
            self.scrape_drama_full(drama_id, drama_info)
        
        # Final stats
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"  Dramas processed: {self.stats['dramas_processed']}")
        print(f"  Episodes downloaded: {self.downloader.stats['episodes']}")
        print(f"  Segments downloaded: {self.downloader.stats['segments']}")
        print(f"  Files uploaded to R2: {self.stats['files_uploaded']}")
        print(f"  Errors: {self.downloader.stats['errors']}")
        print(f"  Time: {elapsed/60:.1f} minutes")
        print(f"  Temp dir: {self.temp_dir}")
        print("="*60)

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="FlickReels Unified Railway Scraper")
    parser.add_argument("--mode", choices=["full", "metadata", "test"], default="test")
    parser.add_argument("--scan", type=int, default=100, help="Navigation IDs to scan (1-N)")
    parser.add_argument("--limit", type=int, help="Max dramas to process")
    parser.add_argument("--drama-ids", type=str, help="Specific drama IDs (comma-separated)")
    
    args = parser.parse_args()
    
    # Create temp directory
    temp_dir = BASE_DIR / "temp_railway_scrape" / datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    scraper = UnifiedScraper(temp_dir)
    
    if args.mode == "test":
        print("=== TEST MODE ===")
        print("[API] Testing connection...")
        result = scraper.api.get_dramas_from_navigation(1)
        print(f"✓ API OK - Found {len(result)} dramas in nav 1")
        
        if HAS_BOTO3:
            print("[R2] Testing connection...")
            try:
                scraper.storage.upload_json("test/connection.json", {
                    "test": True,
                    "time": datetime.now().isoformat()
                })
                print("✓ R2 OK")
            except Exception as e:
                print(f"✗ R2 ERROR: {e}")
        
        print("=== TEST COMPLETE ===")
    
    elif args.mode == "full":
        scraper.run_full_pipeline(
            nav_scan_range=args.scan,
            limit=args.limit
        )

if __name__ == "__main__":
    main()
