#!/usr/bin/env python3
"""
Complete Single Drama Scraper
=============================
Downloads missing episodes for a specific drama and uploads to R2.
Uses root-level format: ep_001.m3u8, ep_001_0000.ts, etc.

Usage:
    python complete_drama.py 5301 "Forbidden Itch"
"""

import os
import sys
import json
import time
import logging
import hashlib
import hmac
import random
import string
import requests
from datetime import datetime
from urllib.parse import urljoin

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("Installing boto3...")
    os.system(f"{sys.executable} -m pip install boto3")
    import boto3
    from botocore.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# R2 Configuration
R2_CONFIG = {
    "account_id": os.environ.get("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key": os.environ.get("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket": os.environ.get("R2_BUCKET_NAME", "asiandrama-cdn"),
}

# FlickReels Config
FLICKREELS_CONFIG = {
    "base_url": "https://api.farsunpteltd.com",
    "secret_key": "tsM5SnqFayhX7c2HfRxm",
    "token": os.environ.get("FLICKREELS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"),
    "version": "2.2.3.0"
}

DEFAULT_DEVICE_PARAMS = {
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


class R2Client:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_CONFIG["access_key"],
            aws_secret_access_key=R2_CONFIG["secret_key"],
            config=Config(signature_version='s3v4', retries={'max_attempts': 3})
        )
        self.bucket = R2_CONFIG["bucket"]
    
    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False
    
    def upload(self, key: str, data: bytes, content_type: str) -> bool:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                CacheControl="public, max-age=31536000"
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed {key}: {e}")
            return False


class FlickReelsAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "version": FLICKREELS_CONFIG["version"],
            "user-agent": "MyUserAgent",
            "content-type": "application/json; charset=UTF-8"
        })
    
    def _sign(self, body: dict, timestamp: str, nonce: str) -> str:
        body_json = json.dumps(body, separators=(',', ':'))
        sorted_data = dict(sorted(json.loads(body_json).items()))
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
        str_d = '_'.join(parts)
        str_b = hashlib.md5(str_d.encode()).hexdigest()
        message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
        return hmac.new(
            FLICKREELS_CONFIG["secret_key"].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def request(self, endpoint: str, extra: dict = None) -> dict:
        body = {**DEFAULT_DEVICE_PARAMS, **(extra or {})}
        timestamp = str(int(time.time()))
        nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        headers = {
            "token": FLICKREELS_CONFIG["token"],
            "sign": self._sign(body, timestamp, nonce),
            "timestamp": timestamp,
            "nonce": nonce
        }
        
        for attempt in range(3):
            try:
                resp = self.session.post(
                    f"{FLICKREELS_CONFIG['base_url']}{endpoint}",
                    json=body,
                    headers=headers,
                    timeout=30
                )
                return resp.json()
            except Exception as e:
                if attempt == 2:
                    return {"status_code": -1, "msg": str(e)}
                time.sleep(1)
        return {"status_code": -1}
    
    def get_episodes(self, drama_id: str) -> list:
        result = self.request("/app/playlet/chapterList", {"playlet_id": drama_id})
        if result.get("status_code") != 1:
            return []
        data = result.get("data", {})
        return data.get("list", []) if isinstance(data, dict) else []
    
    def get_stream_url(self, drama_id: str, chapter_id: str) -> str:
        result = self.request("/app/playlet/play", {
            "playlet_id": drama_id,
            "chapter_id": chapter_id
        })
        if result.get("status_code") != 1:
            return None
        data = result.get("data", {})
        return data.get("hls_url") or data.get("hls")


def download_and_upload_episode(api: FlickReelsAPI, r2: R2Client, 
                                 folder_name: str, drama_id: str, 
                                 episode_num: int, chapter_id: str) -> bool:
    """Download episode and upload to R2 with root-level format"""
    
    prefix = f"flickreels/{folder_name}"
    m3u8_key = f"{prefix}/ep_{episode_num:03d}.m3u8"
    
    # Check if already exists
    if r2.exists(m3u8_key):
        logger.info(f"  [SKIP] Episode {episode_num} already exists")
        return True
    
    # Get HLS URL
    hls_url = api.get_stream_url(drama_id, chapter_id)
    if not hls_url:
        logger.error(f"  [ERROR] No stream URL for episode {episode_num}")
        return False
    
    logger.info(f"  [EP {episode_num}] Downloading...")
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    try:
        # Download m3u8
        resp = session.get(hls_url, timeout=30)
        if resp.status_code != 200:
            logger.error(f"  [ERROR] Failed to get m3u8: {resp.status_code}")
            return False
        
        m3u8_content = resp.text
        base_url = hls_url.rsplit('/', 1)[0] + '/'
        
        # Parse segments
        new_lines = []
        segment_idx = 0
        
        for line in m3u8_content.split('\n'):
            line = line.strip()
            if not line:
                new_lines.append("")
                continue
            
            if line.startswith('#'):
                new_lines.append(line)
                continue
            
            if line.endswith('.ts') or '.ts?' in line:
                # This is a segment
                seg_name = f"ep_{episode_num:03d}_{segment_idx:04d}.ts"
                seg_key = f"{prefix}/{seg_name}"
                
                # Get full URL
                if line.startswith('http'):
                    seg_url = line
                else:
                    seg_url = urljoin(base_url, line)
                
                # Download and upload
                try:
                    seg_resp = session.get(seg_url, timeout=60)
                    if seg_resp.status_code == 200:
                        r2.upload(seg_key, seg_resp.content, "video/MP2T")
                except Exception as e:
                    logger.warning(f"    Segment {segment_idx} failed: {e}")
                
                new_lines.append(seg_name)
                segment_idx += 1
                
                if segment_idx % 10 == 0:
                    print(f"    Progress: {segment_idx} segments", end='\r')
            else:
                new_lines.append(line)
        
        # Upload rewritten m3u8
        new_m3u8 = '\n'.join(new_lines)
        r2.upload(m3u8_key, new_m3u8.encode(), "application/vnd.apple.mpegurl")
        
        logger.info(f"  [EP {episode_num}] ✓ Done ({segment_idx} segments)")
        return True
        
    except Exception as e:
        logger.error(f"  [EP {episode_num}] Failed: {e}")
        return False


def complete_drama(drama_id: str, title: str, start_ep: int = 1):
    """Complete missing episodes for a drama"""
    
    folder_name = f"{title} ({drama_id})"
    logger.info(f"\n{'='*60}")
    logger.info(f"COMPLETING: {folder_name}")
    logger.info(f"Starting from episode: {start_ep}")
    logger.info(f"{'='*60}\n")
    
    api = FlickReelsAPI()
    r2 = R2Client()
    
    # Get episode list
    logger.info("Fetching episode list...")
    episodes = api.get_episodes(drama_id)
    
    if not episodes:
        logger.error("No episodes found!")
        return
    
    logger.info(f"Found {len(episodes)} episodes")
    
    # Process each episode
    done = 0
    failed = 0
    
    for ep in episodes:
        ep_num = ep.get("sort", 1)
        chapter_id = ep.get("id") or ep.get("chapter_id")
        
        if ep_num < start_ep:
            continue
        
        if not chapter_id:
            logger.warning(f"Episode {ep_num} has no chapter_id, skipping")
            continue
        
        if download_and_upload_episode(api, r2, folder_name, drama_id, ep_num, chapter_id):
            done += 1
        else:
            failed += 1
        
        time.sleep(0.3)  # Rate limit
    
    # Update complete.json
    complete_data = {
        "status": "complete",
        "episodes": len(episodes),
        "completed_at": datetime.now().isoformat()
    }
    r2.upload(
        f"flickreels/{folder_name}/complete.json",
        json.dumps(complete_data).encode(),
        "application/json"
    )
    
    logger.info(f"\n{'='*60}")
    logger.info("COMPLETE!")
    logger.info(f"Episodes done: {done}")
    logger.info(f"Episodes failed: {failed}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python complete_drama.py <drama_id> <title> [start_ep]")
        print("Example: python complete_drama.py 5301 'Forbidden Itch' 6")
        sys.exit(1)
    
    drama_id = sys.argv[1]
    title = sys.argv[2]
    start_ep = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    complete_drama(drama_id, title, start_ep)
