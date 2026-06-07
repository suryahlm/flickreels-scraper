#!/usr/bin/env python3
"""
HARVEST ALL - Brute Force ID Scanner (1-7000)
=============================================
Scan SEMUA drama ID, simpan response ke JSON.
TIDAK ada filter bahasa. Panen semua, sortir nanti.

Usage:
    python harvest_all_ids.py                    # Scan 1-7000
    python harvest_all_ids.py --start=5000       # Resume dari ID 5000
    python harvest_all_ids.py --end=8000         # Scan sampai 8000
"""
import sys
sys.path.insert(0, '.')
import json
import time
import argparse
import logging
from pathlib import Path
from local_scraping_indonesia import (
    generate_sign, generate_nonce,
    FLICKREELS_CONFIG, INDONESIAN_BODY,
    rate_limiter
)
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('harvest_all.log', encoding='utf-8')
    ]
)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

OUTPUT_FILE = "harvested_all_dramas.json"
PROGRESS_FILE = "harvest_progress.txt"


def api_request(endpoint, extra_body=None):
    body = {**INDONESIAN_BODY, **(extra_body or {})}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    headers = {
        "token": FLICKREELS_CONFIG["token"],
        "sign": sign, "timestamp": timestamp, "nonce": nonce,
        "version": FLICKREELS_CONFIG["version"],
        "content-type": "application/json"
    }
    try:
        rate_limiter.acquire()
        resp = requests.post(
            f"{FLICKREELS_CONFIG['base_url']}{endpoint}",
            json=body, headers=headers, timeout=15
        )
        return resp.json()
    except Exception as e:
        return {"status_code": -1, "msg": str(e)}


def load_existing_harvest():
    """Load previously harvested data"""
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_harvest(data):
    """Save harvested data to JSON"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_progress(last_id):
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(last_id))


def load_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Harvest All Drama IDs")
    parser.add_argument("--start", type=int, default=1, help="Start ID")
    parser.add_argument("--end", type=int, default=7000, help="End ID")
    parser.add_argument("--resume", action="store_true", help="Resume from last progress")
    args = parser.parse_args()

    # Load existing data
    harvested = load_existing_harvest()
    logger.info(f"Loaded {len(harvested)} previously harvested dramas")

    start_id = args.start
    if args.resume:
        progress = load_progress()
        if progress > 0:
            start_id = progress + 1
            logger.info(f"Resuming from ID {start_id}")

    end_id = args.end

    logger.info("=" * 60)
    logger.info(f"HARVEST ALL - Scanning IDs {start_id} to {end_id}")
    logger.info("=" * 60)

    stats = {
        "scanned": 0,
        "found": 0,
        "not_found": 0,
        "errors": 0,
        "new": 0,
        "consecutive_404": 0,
    }

    start_time = time.time()

    for drama_id in range(start_id, end_id + 1):
        sid = str(drama_id)
        stats["scanned"] += 1

        # Skip if already harvested
        if sid in harvested:
            continue

        result = api_request("/app/playlet/chapterList", {"playlet_id": sid})

        if result.get("status_code") == 1:
            data = result.get("data", {})
            title = data.get("title", "")
            language = data.get("language_name", "")
            episodes = data.get("list", [])

            if title and len(episodes) > 0:
                harvested[sid] = {
                    "id": sid,
                    "title": title,
                    "language_name": language,
                    "cover": data.get("cover", ""),
                    "total_episodes": len(episodes),
                    "episode_ids": [ep.get("chapter_id") for ep in episodes],
                    "start_pay_num": data.get("start_pay_num"),
                    "harvested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                stats["found"] += 1
                stats["new"] += 1
                stats["consecutive_404"] = 0

                # Log every find
                lang_tag = f" [{language}]" if language else " [NO_LANG]"
                logger.info(f"  ✅ ID {drama_id}: {title[:50]}{lang_tag} ({len(episodes)} eps)")
            else:
                stats["not_found"] += 1
                stats["consecutive_404"] += 1
        elif result.get("msg") and "not found" in str(result.get("msg", "")).lower():
            stats["not_found"] += 1
            stats["consecutive_404"] += 1
        else:
            stats["errors"] += 1
            stats["consecutive_404"] = 0

        # Save progress every 100 IDs
        if stats["scanned"] % 100 == 0:
            save_harvest(harvested)
            save_progress(drama_id)
            elapsed = time.time() - start_time
            rate = stats["scanned"] / elapsed if elapsed > 0 else 0
            remaining = (end_id - drama_id) / rate if rate > 0 else 0
            logger.info(
                f"  --- Progress: {drama_id}/{end_id} | "
                f"Found: {stats['found']} | New: {stats['new']} | "
                f"Rate: {rate:.1f} IDs/sec | "
                f"ETA: {remaining/60:.1f} min ---"
            )

        # Don't stop on consecutive 404s — IDs can be sparse
        # Just throttle slightly
        time.sleep(0.08)  # ~12 requests/sec

    # Final save
    save_harvest(harvested)
    save_progress(end_id)

    elapsed = time.time() - start_time
    logger.info(f"\n{'=' * 60}")
    logger.info("HARVEST COMPLETE!")
    logger.info(f"  Scanned: {stats['scanned']}")
    logger.info(f"  Found: {stats['found']}")
    logger.info(f"  New this run: {stats['new']}")
    logger.info(f"  Not found: {stats['not_found']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Total in database: {len(harvested)}")
    logger.info(f"  Time: {elapsed/60:.1f} minutes")
    logger.info(f"  Output: {OUTPUT_FILE}")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
