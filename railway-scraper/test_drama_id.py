#!/usr/bin/env python3
"""Test specific drama ID"""
import sys
sys.path.insert(0, '.')
from batch_scraper_indonesia import FLICKREELS_CONFIG, INDONESIAN_BODY, generate_sign, generate_nonce
import requests
import time

# Test with known ID - Peramal Wanita
drama_id = 5247

body = {
    **INDONESIAN_BODY,
    'playlet_id': str(drama_id)
}

timestamp = str(int(time.time()))
nonce = generate_nonce()
sign = generate_sign(body, timestamp, nonce)

headers = {
    'token': FLICKREELS_CONFIG['token'],
    'sign': sign,
    'timestamp': timestamp,
    'nonce': nonce,
    'version': FLICKREELS_CONFIG['version'],
    'content-type': 'application/json'
}

resp = requests.post(
    f"{FLICKREELS_CONFIG['base_url']}/app/playlet/chapterList",
    json=body,
    headers=headers,
    timeout=15
)
data = resp.json()
print(f'Status: {data.get("status_code")}')
if data.get('data'):
    playlet = data['data']
    print(f"Title: {playlet.get('title')}")
    print(f"Language: {playlet.get('language_name')}")
    chapters = playlet.get('chapters', [])
    print(f"Episodes: {len(chapters)}")
    print(f"Keys in data: {list(playlet.keys())}")
