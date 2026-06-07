#!/usr/bin/env python3
"""
Indonesian Drama ID Scanner
===========================
Scan drama IDs to find Indonesian dramas that might not appear in navigationColumn.
"""
import sys
sys.path.insert(0, '.')
import requests
import json
import hashlib
import hmac
import random
import string
import time
import argparse

from batch_scraper_indonesia import generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY

def check_drama_language(drama_id):
    """Check if a drama ID has Indonesian language version"""
    session = requests.Session()
    
    body = {
        **INDONESIAN_BODY,
        "playlet_id": str(drama_id)
    }
    
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
        resp = session.post(
            f"{FLICKREELS_CONFIG['base_url']}/app/playlet/chapterList",
            json=body,
            headers=headers,
            timeout=15
        )
        data = resp.json()
        
        if data.get("status_code") == 1 and data.get("data"):
            playlet = data["data"]
            title = playlet.get("title", "")
            language = playlet.get("language_name", "")
            episodes = len(playlet.get("chapters", []))
            
            # Check if it's Indonesian
            if language.lower() == "indonesian" or any(indonesian_word in title.lower() for indonesian_word in ['yang', 'dengan', 'itu', 'dan', 'untuk', 'dari']):
                return {
                    "id": drama_id,
                    "title": title,
                    "language": language,
                    "episodes": episodes
                }
    except Exception as e:
        pass
    
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="Start ID")
    parser.add_argument("--end", type=int, default=100, help="End ID")
    args = parser.parse_args()
    
    print(f"Scanning IDs {args.start} to {args.end} for Indonesian dramas...")
    
    found = []
    for drama_id in range(args.start, args.end + 1):
        result = check_drama_language(drama_id)
        if result:
            print(f"  Found: {result['id']} - {result['title'][:50]} ({result['episodes']} eps)")
            found.append(result)
        
        if drama_id % 50 == 0:
            print(f"Progress: {drama_id}/{args.end}")
        
        time.sleep(0.1)  # Rate limit
    
    print(f"\nTotal Indonesian dramas found: {len(found)}")
    
    # Save to file
    if found:
        with open("scanned_indonesia.json", "w", encoding="utf-8") as f:
            json.dump(found, f, ensure_ascii=False, indent=2)
        print(f"Saved to scanned_indonesia.json")

if __name__ == "__main__":
    main()
