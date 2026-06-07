#!/usr/bin/env python3
"""
Search & Scrape Indonesian Dramas ONLY
========================================
Strategy:
  1. Search with Indonesian keywords via /app/user_search/search
  2. Verify EACH result's language via chapterList (language_name == "indonesian")
  3. Also check nav_id=30 and nav_id=12 for remaining Indonesian content
  4. Scrape only confirmed Indonesian dramas

Usage:
    python search_scrape_indonesia.py --discover     # Discovery only (find new IDs)
    python search_scrape_indonesia.py --scrape=5     # Discover + scrape 5 new dramas
"""
import sys
sys.path.insert(0, '.')
import argparse
import time
import json
import logging
from local_scraping_indonesia import (
    IndonesianAPI, LocalIndonesianScraper,
    generate_sign, generate_nonce,
    FLICKREELS_CONFIG, INDONESIAN_BODY, SUPABASE_CONFIG,
    rate_limiter
)
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('search_scrape.log', encoding='utf-8')
    ]
)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)

# Indonesian search keywords (common drama title words)
INDONESIAN_KEYWORDS = [
    "cinta", "suami", "istri", "bos", "mafia", "rahasia",
    "kaisar", "pangeran", "putri", "balas", "dendam", "kembali",
    "aku", "kamu", "dia", "hidup", "hati", "pernikahan",
    "ayah", "ibu", "anak", "pacar", "mantan", "CEO",
    "misteri", "takdir", "warisan", "keluarga", "malam",
    "pesona", "godaan", "mencuri", "permaisuri", "simpan",
    "peramal", "penjaga", "keadilan", "naga", "dewa",
    "bidadari", "pria", "wanita", "gadis", "pemuda",
]


def api_request(endpoint, extra_body=None):
    """Generic API request with signing"""
    body = {**INDONESIAN_BODY, **(extra_body or {})}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)

    headers = {
        "token": FLICKREELS_CONFIG["token"],
        "sign": sign,
        "timestamp": timestamp,
        "nonce": nonce,
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
        logger.error(f"API error: {e}")
        return {"status_code": -1}


def load_existing_ids():
    """Load already scraped drama IDs from Supabase"""
    try:
        resp = requests.get(
            f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
            headers={"apikey": SUPABASE_CONFIG["key"]}
        )
        ids = set()
        if resp.status_code == 200:
            for d in resp.json():
                if d.get('flickreels_id'):
                    ids.add(str(d['flickreels_id']))
        logger.info(f"Loaded {len(ids)} existing drama IDs from Supabase")
        return ids
    except Exception as e:
        logger.error(f"Error loading existing IDs: {e}")
        return set()


def verify_indonesian(drama_id):
    """Verify a drama is Indonesian via chapterList language_name"""
    api = IndonesianAPI()
    detail = api.get_drama_detail(drama_id)
    if not detail:
        return None

    language = detail.get("language_name", "").lower()
    if "indonesian" in language or "indonesia" in language:
        return detail
    return None


def search_indonesian_dramas(existing_ids):
    """Search for Indonesian dramas using keywords, verify each one"""
    candidates = {}  # id -> {title, cover, total_episodes, ...}
    verified_ids = set()  # Confirmed Indonesian
    rejected_ids = set()  # Confirmed NOT Indonesian

    logger.info("=" * 60)
    logger.info("PHASE 1: Search with Indonesian keywords")
    logger.info("=" * 60)

    for kw in INDONESIAN_KEYWORDS:
        for page in range(1, 6):  # Up to 5 pages per keyword
            result = api_request("/app/user_search/search", {
                "keyword": kw,
                "page": page,
                "page_size": 50
            })

            if result.get("status_code") != 1:
                break

            data = result.get("data", {})
            items = data.get("list", []) if isinstance(data, dict) else []
            if not items:
                break

            new_found = 0
            for item in items:
                pid = str(item.get("playlet_id", ""))
                if not pid or pid in existing_ids or pid in candidates or pid in rejected_ids:
                    continue
                candidates[pid] = {
                    "id": pid,
                    "title": item.get("title", ""),
                    "cover": item.get("cover", ""),
                    "total_episodes": int(item.get("upload_num") or 0),
                    "description": item.get("introduce", ""),
                    "tags": item.get("playlet_tag_name", [])
                }
                new_found += 1

            if new_found > 0:
                logger.info(f"  Search \"{kw}\" p{page}: {len(items)} results, {new_found} new candidates")

            if len(items) < 50:
                break
            time.sleep(0.2)
        time.sleep(0.1)

    # Also check nav_id=30 (Indonesian feed) for any remaining
    logger.info(f"\nAlso checking nav_id=30 and nav_id=12...")
    for nav_id in ["30", "12"]:
        for page in range(1, 20):
            result = api_request("/app/playlet/navigationColumn", {
                "navigation_id": nav_id,
                "page": page,
                "page_size": 50
            })
            if result.get("status_code") != 1:
                break
            data = result.get("data", [])
            if not data:
                break
            found = 0
            for section in data:
                for item in section.get("list", []):
                    pid = str(item.get("playlet_id", ""))
                    if pid and pid not in existing_ids and pid not in candidates:
                        candidates[pid] = {
                            "id": pid,
                            "title": item.get("title", ""),
                            "cover": item.get("cover", ""),
                            "total_episodes": int(item.get("upload_num") or 0),
                            "description": item.get("introduce", ""),
                            "tags": item.get("playlet_tag_name", [])
                        }
                        found += 1
            if found > 0:
                logger.info(f"  nav_id={nav_id} p{page}: {found} new candidates")
            time.sleep(0.2)

    logger.info(f"\nTotal candidates before verification: {len(candidates)}")

    # PHASE 2: Verify each candidate is Indonesian
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Verifying language (indonesian only)")
    logger.info("=" * 60)

    confirmed = []
    for pid, drama in candidates.items():
        detail = verify_indonesian(pid)
        if detail:
            drama["episodes_detail"] = detail.get("episodes", [])
            drama["cover"] = drama.get("cover") or detail.get("cover", "")
            confirmed.append(drama)
            logger.info(f"  ✅ [{pid}] {drama['title'][:40]} — INDONESIAN ({len(detail.get('episodes', []))} eps)")
        else:
            rejected_ids.add(pid)
            logger.info(f"  ❌ [{pid}] {drama['title'][:40]} — not Indonesian, skip")
        time.sleep(0.2)

    logger.info(f"\nVerified Indonesian: {len(confirmed)} / {len(candidates)} candidates")
    return confirmed


def main():
    parser = argparse.ArgumentParser(description="Search & Scrape Indonesian Dramas")
    parser.add_argument("--discover", action="store_true", help="Discovery only (no scraping)")
    parser.add_argument("--scrape", type=int, default=0, help="Discover + scrape N new dramas")
    args = parser.parse_args()

    existing_ids = load_existing_ids()

    # Discovery
    indonesian_dramas = search_indonesian_dramas(existing_ids)

    if not indonesian_dramas:
        logger.info("No new Indonesian dramas found!")
        return

    # Save discovery results
    with open("discovered_indonesian.json", "w", encoding="utf-8") as f:
        json.dump(indonesian_dramas, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(indonesian_dramas)} dramas to discovered_indonesian.json")

    if args.discover:
        logger.info("\nDiscovery-only mode. Use --scrape=N to scrape.")
        return

    # Scrape
    limit = args.scrape or len(indonesian_dramas)
    scraper = LocalIndonesianScraper()

    logger.info(f"\n{'=' * 60}")
    logger.info(f"PHASE 3: Scraping {min(limit, len(indonesian_dramas))} Indonesian dramas")
    logger.info(f"{'=' * 60}\n")

    success_count = 0
    for drama in indonesian_dramas[:limit]:
        logger.info(f"\n[{success_count + 1}/{limit}] {drama['title']} (ID: {drama['id']})")
        if scraper.scrape_drama(drama):
            success_count += 1
            logger.info(f"✅ SUCCESS ({success_count}/{limit})")
        else:
            logger.warning(f"⚠️ SKIPPED/FAILED")

        if success_count >= limit:
            break

    logger.info(f"\n{'=' * 60}")
    logger.info(f"COMPLETE: {success_count}/{limit} dramas scraped")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
