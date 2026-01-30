"""
FlickReels Indonesian Drama Scraper

Scrapes drama list and details using language_id=6 (Indonesian).
Saves to dramas_indonesia.json with complete cover URLs.
"""

import hashlib
import hmac
import json
import random
import string
import time
import requests
from typing import Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "https://api.farsunpteltd.com"
SIGN_SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"
VERSION = "2.2.3.0"
USER_AGENT = "MyUserAgent"

# Token from admin server (working)
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"

DEFAULT_BODY_PARAMS = {
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


def get_navigation_dramas(navigation_id: int, page: int = 1) -> List[Dict]:
    """Get dramas from a navigation category."""
    result = api_request("/app/playlet/navigationColumn", {
        "navigation_id": navigation_id,
        "page": page,
        "page_size": 50
    })
    
    dramas = []
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
                    "hls_url": ep.get("hls_url", "")
                })
    
    return episodes, drama_cover


def get_episode_stream(playlet_id: str, chapter_id: str) -> Dict:
    """Get HLS stream URL for an episode."""
    result = api_request("/app/playlet/play", {
        "playlet_id": playlet_id,
        "chapter_id": chapter_id,
        "chapter_type": 0,
        "auto_unlock": False,
        "fragmentPosition": 0,
        "show_type": 0,
        "source": 1
    })
    
    if result.get("status_code") == 1 and result.get("data"):
        data = result["data"]
        return {
            "hls_url": data.get("hls_url"),
            "cover_url": data.get("cover_url"),
            "duration": data.get("duration", 0)
        }
    
    return {}


# ============================================================================
# MAIN SCRAPER
# ============================================================================

def scrape_indonesian_dramas(max_dramas: int = 20, max_episodes_per_drama: int = 5):
    """
    Scrape Indonesian dramas with their episodes and stream URLs.
    
    Args:
        max_dramas: Maximum number of dramas to scrape
        max_episodes_per_drama: Maximum episodes to scrape per drama (for HLS URLs)
    """
    print("=" * 60)
    print("FlickReels Indonesian Drama Scraper")
    print(f"Language ID: 6 (Indonesian)")
    print("=" * 60)
    
    # Get drama list
    all_dramas = get_hot_rank_dramas()
    
    # Dedupe by playlet_id
    seen_ids = set()
    unique_dramas = []
    for d in all_dramas:
        if d["playlet_id"] not in seen_ids:
            seen_ids.add(d["playlet_id"])
            unique_dramas.append(d)
    
    print(f"\n[INFO] {len(unique_dramas)} unique dramas found")
    
    # Limit
    dramas_to_scrape = unique_dramas[:max_dramas]
    print(f"[INFO] Scraping {len(dramas_to_scrape)} dramas...")
    
    result = {}
    
    for i, drama in enumerate(dramas_to_scrape):
        playlet_id = drama["playlet_id"]
        print(f"\n[{i+1}/{len(dramas_to_scrape)}] {drama['title']} (ID: {playlet_id})")
        
        # Get episodes and drama cover
        episodes, drama_cover = get_drama_episodes(playlet_id)
        print(f"  Found {len(episodes)} episodes")
        
        # Use drama_cover if available, otherwise use cover from list
        final_cover = drama_cover or drama.get("cover_url")
        
        # Episodes from chapterList already have hls_url, just use them directly
        # Build drama object
        result[playlet_id] = {
            "playlet_id": playlet_id,
            "title": drama["title"],
            "cover_url": final_cover,
            "chapter_total": drama["chapter_total"],
            "description": drama.get("description", ""),
            "language": "id",
            "episodes": episodes
        }
        
        time.sleep(0.5)  # Rate limit between dramas
    
    # Save to file
    output_file = "dramas_indonesia.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"\n{'=' * 60}")
    print(f"[DONE] Scraped {len(result)} Indonesian dramas")
    print(f"[DONE] Saved to {output_file}")
    print(f"{'=' * 60}")
    
    return result


if __name__ == "__main__":
    # Scrape 20 dramas with 5 episodes each for demo
    scrape_indonesian_dramas(max_dramas=20, max_episodes_per_drama=5)
