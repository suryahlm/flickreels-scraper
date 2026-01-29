"""
FlickReels Indonesian Scraper → R2 Uploader
===========================================

Scrapes Indonesian dramas (language_id=6) and uploads to Cloudflare R2.
Designed to run on Railway.

Usage:
    python railway_scraper.py           # Scrape all and upload to R2
    python railway_scraper.py --max=50  # Limit to 50 dramas
"""

import hashlib
import hmac
import json
import os
import random
import string
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "https://api.farsunpteltd.com"
SIGN_SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"
VERSION = "2.2.3.0"
USER_AGENT = "MyUserAgent"

TOKEN = os.getenv("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU")

# R2 Configuration
R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "asiandrama-cdn"),
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com"
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
    "language_id": "6"  # INDONESIAN ONLY
}

# ============================================================================
# R2 STORAGE
# ============================================================================

try:
    import boto3
    from botocore.config import Config
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("[WARN] boto3 not installed, will save locally only")

def upload_to_r2(data: dict, path: str = "flickreels/dramas.json") -> bool:
    """Upload JSON data to R2."""
    if not HAS_BOTO3:
        print("[WARN] boto3 not available, skipping R2 upload")
        return False
    
    try:
        client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG["endpoint_url"],
            aws_access_key_id=R2_CONFIG["access_key_id"],
            aws_secret_access_key=R2_CONFIG["secret_access_key"],
            config=Config(signature_version='s3v4')
        )
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        client.put_object(
            Bucket=R2_CONFIG["bucket_name"],
            Key=path,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        
        print(f"[R2] Uploaded {len(data)} dramas to {path}")
        return True
        
    except Exception as e:
        print(f"[R2 ERROR] Upload failed: {e}")
        return False

# ============================================================================
# CRYPTO FUNCTIONS
# ============================================================================

def generate_nonce(length: int = 32) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def _method_d(body_json: str) -> str:
    if not body_json or body_json == "{}":
        return ""
    try:
        data = json.loads(body_json)
    except:
        return ""
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

def generate_sign(body: Dict, timestamp: int, nonce: str) -> str:
    body_json = json.dumps(body, separators=(',', ':'))
    str_d = _method_d(body_json)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    sign = hmac.new(
        SIGN_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return sign

# ============================================================================
# API REQUEST
# ============================================================================

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json; charset=UTF-8",
    "Accept-Encoding": "gzip",
    "User-Agent": USER_AGENT,
    "Cache-Control": "no-cache",
    "version": VERSION
})

def api_request(endpoint: str, body: Dict = {}) -> Dict:
    """Make authenticated request to FlickReels API."""
    url = f"{BASE_URL}{endpoint}"
    timestamp = int(time.time())
    nonce = generate_nonce()
    
    full_body = {**DEFAULT_BODY_PARAMS, **body}
    sign = generate_sign(full_body, timestamp, nonce)
    
    headers = {
        "token": TOKEN,
        "sign": sign,
        "timestamp": str(timestamp),
        "nonce": nonce
    }
    
    try:
        response = session.post(url, json=full_body, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return {"status_code": -1, "msg": str(e), "data": None}

# ============================================================================
# DRAMA FETCHING
# ============================================================================

def get_hot_rank_dramas() -> List[Dict]:
    """Get hot ranking dramas (Indonesian)."""
    print("[INFO] Fetching hot rank dramas...")
    result = api_request("/app/playlet/hotRank", {"rank_type": 0})
    
    dramas = []
    if result.get("status_code") == 1 and result.get("data"):
        for rank in result["data"]:
            for drama in rank.get("data", []):
                dramas.append({
                    "playlet_id": drama.get("playlet_id"),
                    "title": drama.get("title"),
                    "cover_url": drama.get("cover_url"),
                    "chapter_total": drama.get("chapter_total"),
                    "description": drama.get("description", "")
                })
    
    print(f"[INFO] Found {len(dramas)} dramas from hot rank")
    return dramas

def get_navigation_dramas(start_nav: int = 1, end_nav: int = 100) -> List[Dict]:
    """Get dramas from navigation categories."""
    print(f"[INFO] Scanning navigation IDs {start_nav} to {end_nav}...")
    dramas = []
    
    for nav_id in range(start_nav, end_nav + 1):
        result = api_request("/app/playlet/navigationColumn", {
            "navigation_id": nav_id,
            "page": 1,
            "page_size": 50
        })
        
        if result.get("status_code") == 1 and result.get("data"):
            for column in result["data"]:
                for drama in column.get("list", []):
                    dramas.append({
                        "playlet_id": drama.get("playlet_id"),
                        "title": drama.get("title"),
                        "cover_url": drama.get("cover_url"),
                        "chapter_total": drama.get("chapter_total"),
                        "description": drama.get("description", "")
                    })
        
        if nav_id % 20 == 0:
            print(f"  Progress: nav {nav_id}, found {len(dramas)} dramas")
        
        time.sleep(0.2)
    
    return dramas

def get_drama_episodes(playlet_id: str) -> tuple:
    """Get episode list for a drama. Returns (episodes, drama_cover)."""
    result = api_request("/app/playlet/chapterList", {
        "playlet_id": playlet_id
    })
    
    episodes = []
    drama_cover = None
    
    if result.get("status_code") == 1 and result.get("data"):
        data = result["data"]
        drama_cover = data.get("cover") or data.get("process_cover")
        
        episode_list = data.get("list", [])
        for ep in episode_list:
            if isinstance(ep, dict):
                episodes.append({
                    "chapter_id": ep.get("chapter_id"),
                    "title": ep.get("title", f"EP.{ep.get('sort', 1)}"),
                    "chapter_num": ep.get("sort", 1),
                    "duration": ep.get("duration", 0),
                    "cover_url": ep.get("cover_url", ""),
                    "hls_url": ep.get("hls_url", ""),
                    "is_free": ep.get("is_free", 0),
                    "is_vip": ep.get("is_vip", 0)
                })
    
    return episodes, drama_cover

# ============================================================================
# MAIN SCRAPER
# ============================================================================

def scrape_and_upload(max_dramas: int = None, scan_range: int = 100):
    """
    Scrape Indonesian dramas and upload to R2.
    
    Args:
        max_dramas: Maximum number of dramas to scrape (None = all)
        scan_range: Navigation ID range to scan
    """
    print("=" * 60)
    print("FlickReels Indonesian Drama Scraper → R2")
    print(f"Language ID: 6 (Indonesian)")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Get drama list from multiple sources
    all_dramas = []
    all_dramas.extend(get_hot_rank_dramas())
    all_dramas.extend(get_navigation_dramas(1, scan_range))
    
    # Dedupe by playlet_id
    seen_ids = set()
    unique_dramas = []
    for d in all_dramas:
        pid = str(d.get("playlet_id"))
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique_dramas.append(d)
    
    print(f"\n[INFO] {len(unique_dramas)} unique dramas found")
    
    # Limit if specified
    if max_dramas:
        unique_dramas = unique_dramas[:max_dramas]
    
    print(f"[INFO] Scraping {len(unique_dramas)} dramas...\n")
    
    result = {}
    
    for i, drama in enumerate(unique_dramas):
        playlet_id = str(drama["playlet_id"])
        print(f"[{i+1}/{len(unique_dramas)}] {drama['title']}")
        
        # Get episodes and drama cover
        episodes, drama_cover = get_drama_episodes(playlet_id)
        
        # Use drama_cover if available
        final_cover = drama_cover or drama.get("cover_url")
        
        # Build drama object
        result[playlet_id] = {
            "title": drama["title"],
            "cover_url": final_cover,
            "chapter_total": len(episodes) or drama.get("chapter_total", 0),
            "description": drama.get("description", ""),
            "language": "id",
            "episodes": episodes
        }
        
        # Progress update every 10 dramas
        if (i + 1) % 10 == 0:
            print(f"  → Progress: {i+1}/{len(unique_dramas)} dramas processed")
        
        time.sleep(0.3)  # Rate limit
    
    print(f"\n{'=' * 60}")
    print(f"[DONE] Scraped {len(result)} Indonesian dramas")
    
    # Save locally as backup
    local_file = "dramas_indonesia_r2.json"
    with open(local_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[LOCAL] Saved to {local_file}")
    
    # Upload to R2
    if upload_to_r2(result, "flickreels/dramas.json"):
        print("[R2] Successfully uploaded to R2!")
    else:
        print("[R2] Upload failed, but local file saved")
    
    print(f"\n[FINISHED] {datetime.now().isoformat()}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    import sys
    
    max_dramas = None
    scan_range = 100
    
    # Parse arguments
    for arg in sys.argv[1:]:
        if arg.startswith("--max="):
            max_dramas = int(arg.split("=")[1])
        elif arg.startswith("--scan="):
            scan_range = int(arg.split("=")[1])
    
    scrape_and_upload(max_dramas=max_dramas, scan_range=scan_range)
