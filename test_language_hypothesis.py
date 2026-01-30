"""
Test script to compare FlickReels drama lists between different language_id values.
Hypothesis: Different languages may return different drama_id for the same drama title.
"""

import hashlib
import hmac
import json
import random
import string
import time
import requests

FLICKREELS_BASE_URL = "https://api.farsunpteltd.com"
SIGN_SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"
USER_AGENT = "MyUserAgent"
VERSION = "2.2.3.0"
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.gPxsB-d_6-DRxuSuBLxs-xjN5lhEyPdgGPZGBKsj_kg"

def generate_nonce(length=32):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def _method_d(body_json):
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


def generate_sign(body, timestamp, nonce):
    body_json = json.dumps(body, separators=(',',':'))
    str_d = _method_d(body_json)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    sign = hmac.new(
        SIGN_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return sign


def flickreels_request(endpoint, extra_body, language_id="6"):
    body = {
        "main_package_id": 100,
        "device_id": "0d209b4d4009b44c",
        "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
        "os": "android",
        "device_brand": "samsung",
        "device_number": "9",
        "device_model": "SM-X710N",
        "countryCode": "ID",
        **extra_body,
        "language_id": language_id  # Set LAST to ensure it's not overridden
    }
    
    timestamp = str(int(time.time()))
    nonce = generate_nonce(32)
    sign = generate_sign(body, timestamp, nonce)
    
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept-Encoding': 'gzip',
        'User-Agent': USER_AGENT,
        'Cache-Control': 'no-cache',
        'version': VERSION,
        'token': TOKEN,
        'sign': sign,
        'timestamp': timestamp,
        'nonce': nonce,
    }
    
    url = f"{FLICKREELS_BASE_URL}{endpoint}"
    response = requests.post(url, headers=headers, json=body)
    return response.json()


def get_hot_rank_dramas(language_id):
    """Get hot ranking dramas for a specific language."""
    result = flickreels_request("/app/playlet/hotRank", {
        "rank_type": 0,
    }, language_id=language_id)
    
    dramas = []
    if result.get("status_code") == 1 and result.get("data"):
        for rank in result["data"]:
            for drama in rank.get("data", []):
                dramas.append({
                    "playlet_id": drama.get("playlet_id"),
                    "title": drama.get("title"),
                    "chapter_total": drama.get("chapter_total")
                })
    return dramas


def get_navigation_dramas(navigation_id, language_id):
    """Get dramas from a navigation/category."""
    result = flickreels_request("/app/playlet/navigationColumn", {
        "navigation_id": navigation_id,
        "page": 1,
        "page_size": 20
    }, language_id=language_id)
    
    dramas = []
    if result.get("status_code") == 1 and result.get("data"):
        for column in result["data"]:
            for drama in column.get("list", []):
                dramas.append({
                    "playlet_id": drama.get("playlet_id"),
                    "title": drama.get("title"),
                    "chapter_total": drama.get("chapter_total")
                })
    return dramas


def compare_language_drama_ids():
    """Compare drama IDs between different languages."""
    print("=" * 70)
    print("TESTING HYPOTHESIS: Different language_id returns different drama_id")
    print("=" * 70)
    
    # Test Hot Rank
    print("\n[1] Fetching Hot Rank with language_id=6 (Indonesian)...")
    dramas_id = get_hot_rank_dramas("6")
    print(f"    Found {len(dramas_id)} dramas")
    for d in dramas_id[:5]:
        print(f"    - ID: {d['playlet_id']}, Title: {d['title']}")
    
    time.sleep(1)
    
    print("\n[2] Fetching Hot Rank with language_id=1...")
    dramas_en = get_hot_rank_dramas("1")
    print(f"    Found {len(dramas_en)} dramas")
    for d in dramas_en[:5]:
        print(f"    - ID: {d['playlet_id']}, Title: {d['title']}")
    
    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON:")
    
    ids_lang6 = set(d['playlet_id'] for d in dramas_id)
    ids_lang1 = set(d['playlet_id'] for d in dramas_en)
    
    common = ids_lang6 & ids_lang1
    only_in_6 = ids_lang6 - ids_lang1
    only_in_1 = ids_lang1 - ids_lang6
    
    print(f"  Common IDs: {len(common)}")
    print(f"  Only in language_id=6: {len(only_in_6)}")
    print(f"  Only in language_id=1: {len(only_in_1)}")
    
    if only_in_6 or only_in_1:
        print("\n*** DIFFERENT DRAMA IDs FOUND! ***")
        print("This confirms different languages have different drama_id!")
        if only_in_6:
            print(f"\n  IDs only in Indonesian: {list(only_in_6)[:10]}")
        if only_in_1:
            print(f"\n  IDs only in English: {list(only_in_1)[:10]}")
    else:
        print("\n  Same drama IDs for both languages.")
        print("  Hypothesis NOT confirmed - need to investigate further.")
    
    # Check title differences for same IDs
    print("\n" + "=" * 70)
    print("TITLE COMPARISON for common IDs:")
    
    titles_6 = {d['playlet_id']: d['title'] for d in dramas_id}
    titles_1 = {d['playlet_id']: d['title'] for d in dramas_en}
    
    title_diffs = 0
    for pid in list(common)[:10]:
        t6 = titles_6.get(pid, "N/A")
        t1 = titles_1.get(pid, "N/A")
        if t6 != t1:
            print(f"  ID {pid}:")
            print(f"    lang=6: {t6}")
            print(f"    lang=1: {t1}")
            title_diffs += 1
    
    if title_diffs == 0:
        print("  No title differences found for common IDs")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    compare_language_drama_ids()
