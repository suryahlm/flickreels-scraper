"""
Test script to compare FlickReels API responses with different language_id values.
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

DEFAULT_DEVICE_PARAMS = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID"
}


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
    body = {**DEFAULT_DEVICE_PARAMS, "language_id": language_id, **extra_body}
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


def test_language_comparison():
    """Test if different language_id returns different HLS URLs."""
    playlet_id = "1007"  # Love Trap with My Dashing Knight
    chapter_id = "76075"  # Episode 1
    
    print("=" * 60)
    print("Testing FlickReels language_id behavior")
    print("=" * 60)
    
    extra_body = {
        "playlet_id": playlet_id,
        "chapter_id": chapter_id,
        "chapter_type": 0,
        "auto_unlock": False,
        "fragmentPosition": 0,
        "show_type": 0,
        "source": 1,
        "vip_btn_scene": '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
    }
    
    # Test with language_id = 6 (Indonesian)
    print("\n[1] Testing with language_id = 6 (Indonesian)...")
    result_id = flickreels_request("/app/playlet/play", extra_body, language_id="6")
    if result_id.get("status_code") == 1:
        hls_url_id = result_id.get("data", {}).get("hls_url", "N/A")
        title_id = result_id.get("data", {}).get("chapter_title", "N/A")
        print(f"   Title: {title_id}")
        print(f"   HLS URL: {hls_url_id[:100]}...")
    else:
        print(f"   Error: {result_id}")
    
    time.sleep(1)
    
    # Test with language_id = 1 (What language?)
    print("\n[2] Testing with language_id = 1...")
    result_en = flickreels_request("/app/playlet/play", extra_body, language_id="1")
    if result_en.get("status_code") == 1:
        hls_url_en = result_en.get("data", {}).get("hls_url", "N/A")
        title_en = result_en.get("data", {}).get("chapter_title", "N/A")
        print(f"   Title: {title_en}")
        print(f"   HLS URL: {hls_url_en[:100]}...")
    else:
        print(f"   Error: {result_en}")
    
    time.sleep(1)
    
    # Test with language_id = 2
    print("\n[3] Testing with language_id = 2...")
    result_2 = flickreels_request("/app/playlet/play", extra_body, language_id="2")
    if result_2.get("status_code") == 1:
        hls_url_2 = result_2.get("data", {}).get("hls_url", "N/A")
        title_2 = result_2.get("data", {}).get("chapter_title", "N/A")
        print(f"   Title: {title_2}")
        print(f"   HLS URL: {hls_url_2[:100]}...")
    else:
        print(f"   Error: {result_2}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    
    # Compare HLS URLs
    if result_id.get("status_code") == 1 and result_en.get("status_code") == 1:
        hls_id = result_id.get("data", {}).get("hls_url", "")
        hls_en = result_en.get("data", {}).get("hls_url", "")
        
        if hls_id == hls_en:
            print("! HLS URLs are IDENTICAL for language_id 1 and 6")
            print("! This means subtitle is HARDCODED into the video file")
            print("! language_id likely only affects TITLE translation, not subtitle")
        else:
            print("✓ HLS URLs are DIFFERENT!")
            print("  Subtitle should change based on language_id")
    
    print("=" * 60)


if __name__ == "__main__":
    test_language_comparison()
