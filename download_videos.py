"""
FlickReels HLS Video Downloader

Downloads HLS video segments from FlickReels CDN based on scraped metadata.
Fetches FRESH HLS URLs from API (tokens expire quickly).
Saves to local folder structure for later upload to R2.

Usage:
    python download_videos.py                    # Download all dramas
    python download_videos.py --drama-ids 2858,533,487  # Download specific dramas
    python download_videos.py --max-dramas 5     # Download first 5 dramas only
"""

import argparse
import hashlib
import hmac
import json
import os
import random
import re
import string
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT_FILE = BASE_DIR / "dramas_indonesia.json"
DEFAULT_OUTPUT_DIR = BASE_DIR / "Scraping" / datetime.now().strftime("%Y-%m-%d")

# Request settings
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

# User agent to mimic browser
USER_AGENT = "FlickReels/2.2.3.0 (Android 13; en)"

# ============================================================================
# FLICKREELS API - Import from working scraper
# ============================================================================

# Import API functions from scrape_indonesia.py (known working implementation)
try:
    from scrape_indonesia import get_episode_stream
    
    def get_fresh_hls_url(playlet_id: str, chapter_id: str) -> Optional[str]:
        """Get fresh HLS URL with valid token from API."""
        result = get_episode_stream(playlet_id, chapter_id)
        return result.get("hls_url")
        
    print("[INFO] Using API from scrape_indonesia.py")
except ImportError:
    print("[ERROR] Could not import scrape_indonesia.py!")
    
    def get_fresh_hls_url(playlet_id: str, chapter_id: str) -> Optional[str]:
        return None

def sanitize_filename(name: str) -> str:
    """Remove/replace characters that are invalid for folder names."""
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Remove leading/trailing whitespace and dots
    name = name.strip().strip('.')
    # Limit length to avoid path issues
    if len(name) > 100:
        name = name[:100]
    return name

# ============================================================================
# DOWNLOADER CLASS
# ============================================================================

class HLSDownloader:
    def __init__(self, output_dir: Path, input_file: Path):
        self.output_dir = output_dir
        self.input_file = input_file
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
        })
        
        # Statistics
        self.stats = {
            "dramas_processed": 0,
            "episodes_downloaded": 0,
            "segments_downloaded": 0,
            "bytes_downloaded": 0,
            "errors": 0
        }
    
    def load_dramas(self) -> Dict:
        """Load drama metadata from JSON file."""
        print(f"\n[INFO] Loading dramas from: {self.input_file}")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[INFO] Found {len(data)} dramas")
        return data
    
    def download_file(self, url: str, output_path: Path) -> bool:
        """Download a single file with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=TIMEOUT, stream=True)
                response.raise_for_status()
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            self.stats["bytes_downloaded"] += len(chunk)
                
                return True
                
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"    [ERROR] Failed to download {url}: {e}")
                    self.stats["errors"] += 1
                    return False
        
        return False
    
    def parse_m3u8(self, content: str, base_url: str) -> List[str]:
        """Parse M3U8 manifest and extract segment URLs."""
        segments = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue
            # This is a segment URL
            if line.endswith('.ts') or '.ts?' in line:
                # Handle relative URLs
                if not line.startswith('http'):
                    segment_url = urljoin(base_url, line)
                else:
                    segment_url = line
                segments.append(segment_url)
        
        return segments
    
    def rewrite_m3u8(self, content: str, segment_prefix: str) -> str:
        """Rewrite M3U8 manifest to use local segment paths."""
        lines = content.strip().split('\n')
        new_lines = []
        segment_index = 0
        
        for line in lines:
            line = line.strip()
            if line.endswith('.ts') or '.ts?' in line:
                # Replace with local filename
                new_lines.append(f"{segment_prefix}_{segment_index:04d}.ts")
                segment_index += 1
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def download_episode(self, drama_id: str, ep_num: int, hls_url: str) -> bool:
        """Download a complete episode (manifest + all segments)."""
        episode_dir = self.output_dir / "videos" / drama_id
        episode_prefix = f"ep_{ep_num:03d}"
        manifest_path = episode_dir / f"{episode_prefix}.m3u8"
        
        # Skip if already downloaded
        if manifest_path.exists():
            print(f"    [SKIP] Episode {ep_num} already exists")
            return True
        
        try:
            # 1. Download manifest
            response = self.session.get(hls_url, timeout=TIMEOUT)
            response.raise_for_status()
            manifest_content = response.text
            
            # 2. Parse segments
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            segments = self.parse_m3u8(manifest_content, base_url)
            
            if not segments:
                print(f"    [WARN] No segments found in manifest for episode {ep_num}")
                return False
            
            # 3. Download segments
            print(f"    Downloading {len(segments)} segments...")
            for i, segment_url in enumerate(segments):
                segment_path = episode_dir / f"{episode_prefix}_{i:04d}.ts"
                if not self.download_file(segment_url, segment_path):
                    return False
                self.stats["segments_downloaded"] += 1
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"      Progress: {i + 1}/{len(segments)} segments")
            
            # 4. Save rewritten manifest
            new_manifest = self.rewrite_m3u8(manifest_content, episode_prefix)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(new_manifest)
            
            self.stats["episodes_downloaded"] += 1
            return True
            
        except Exception as e:
            print(f"    [ERROR] Failed to download episode {ep_num}: {e}")
            self.stats["errors"] += 1
            return False
    
    def download_drama(self, drama_id: str, drama_data: Dict, max_episodes: Optional[int] = None) -> bool:
        """Download all episodes of a drama."""
        title = drama_data.get("title", "Unknown")
        episodes = drama_data.get("episodes", [])
        
        if not episodes:
            print(f"  [WARN] No episodes found for {title}")
            return False
        
        if max_episodes:
            episodes = episodes[:max_episodes]
        
        print(f"\n[DRAMA] {title} (ID: {drama_id})")
        print(f"  Episodes to download: {len(episodes)}")
        
        # Save drama metadata - use title as folder name for better organization
        folder_name = sanitize_filename(f"{title} ({drama_id})")
        drama_dir = self.output_dir / folder_name
        drama_dir.mkdir(parents=True, exist_ok=True)
        
        meta_path = drama_dir / "metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({
                "playlet_id": drama_id,
                "title": title,
                "cover_url": drama_data.get("cover_url", ""),
                "total_episodes": len(drama_data.get("episodes", []))
            }, f, indent=2, ensure_ascii=False)
        
        # Download each episode
        for i, episode in enumerate(episodes):
            ep_num = i + 1
            chapter_id = episode.get("chapter_id", "")
            
            if not chapter_id:
                print(f"  [SKIP] Episode {ep_num} - no chapter_id")
                continue
            
            print(f"  [EP {ep_num}/{len(episodes)}] Fetching fresh URL...")
            
            # Get FRESH HLS URL from API (stored URLs have expired tokens)
            hls_url = get_fresh_hls_url(drama_id, chapter_id)
            
            if not hls_url:
                print(f"    [ERROR] Failed to get HLS URL for episode {ep_num}")
                self.stats["errors"] += 1
                continue
            
            print(f"    Downloading...")
            self.download_episode(drama_id, ep_num, hls_url)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        self.stats["dramas_processed"] += 1
        return True
    
    def download_all(self, drama_ids: Optional[List[str]] = None, 
                     max_dramas: Optional[int] = None,
                     max_episodes_per_drama: Optional[int] = None):
        """Download all or selected dramas."""
        dramas = self.load_dramas()
        
        # Filter by drama IDs if specified
        if drama_ids:
            dramas = {k: v for k, v in dramas.items() if k in drama_ids}
            print(f"[INFO] Filtered to {len(dramas)} dramas")
        
        # Limit number of dramas
        if max_dramas:
            drama_items = list(dramas.items())[:max_dramas]
            dramas = dict(drama_items)
            print(f"[INFO] Limited to {len(dramas)} dramas")
        
        print(f"\n{'='*60}")
        print(f"Starting download of {len(dramas)} dramas")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main dramas.json (metadata only, no HLS URLs for security)
        dramas_meta = {}
        for drama_id, data in dramas.items():
            dramas_meta[drama_id] = {
                "playlet_id": drama_id,
                "title": data.get("title", ""),
                "cover_url": data.get("cover_url", ""),
                "total_episodes": len(data.get("episodes", [])),
                "language": data.get("language", "id")
            }
        
        with open(self.output_dir / "dramas.json", 'w', encoding='utf-8') as f:
            json.dump(dramas_meta, f, indent=2, ensure_ascii=False)
        
        # Download each drama
        start_time = time.time()
        
        for drama_id, drama_data in dramas.items():
            self.download_drama(drama_id, drama_data, max_episodes_per_drama)
        
        elapsed = time.time() - start_time
        
        # Print statistics
        print(f"\n{'='*60}")
        print(f"DOWNLOAD COMPLETE")
        print(f"{'='*60}")
        print(f"  Dramas processed:    {self.stats['dramas_processed']}")
        print(f"  Episodes downloaded: {self.stats['episodes_downloaded']}")
        print(f"  Segments downloaded: {self.stats['segments_downloaded']}")
        print(f"  Total data:          {self.stats['bytes_downloaded'] / (1024*1024):.1f} MB")
        print(f"  Errors:              {self.stats['errors']}")
        print(f"  Time elapsed:        {elapsed/60:.1f} minutes")
        print(f"  Output:              {self.output_dir}")
        print(f"{'='*60}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Download FlickReels HLS videos")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT_FILE),
                        help="Input JSON file with drama metadata")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_DIR),
                        help="Output directory for downloaded videos")
    parser.add_argument("--drama-ids", type=str, default=None,
                        help="Comma-separated drama IDs to download (e.g., 2858,533,487)")
    parser.add_argument("--max-dramas", type=int, default=None,
                        help="Maximum number of dramas to download")
    parser.add_argument("--max-episodes", type=int, default=None,
                        help="Maximum episodes per drama to download")
    
    args = parser.parse_args()
    
    # Parse drama IDs
    drama_ids = None
    if args.drama_ids:
        drama_ids = [x.strip() for x in args.drama_ids.split(',')]
    
    # Create downloader
    downloader = HLSDownloader(
        output_dir=Path(args.output),
        input_file=Path(args.input)
    )
    
    # Run download
    downloader.download_all(
        drama_ids=drama_ids,
        max_dramas=args.max_dramas,
        max_episodes_per_drama=args.max_episodes
    )


if __name__ == "__main__":
    main()
