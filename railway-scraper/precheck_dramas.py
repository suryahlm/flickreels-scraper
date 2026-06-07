#!/usr/bin/env python3
"""
Pre-check: Cek mana dari 77 drama yang masih HIDUP (bisa di-stream)
Menghapus drama mati dari list dan update new_indonesian_clean.json
"""
import sys
sys.path.insert(0, '.')
import json
import time
import requests
from batch_scraper_indonesia import (
    IndonesianAPI, SUPABASE_CONFIG, rate_limiter,
    generate_sign, generate_nonce, FLICKREELS_CONFIG, INDONESIAN_BODY
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Load list
with open('new_indonesian_clean.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

logger.info(f"Checking {len(dramas)} dramas...")

# Load existing IDs from Supabase
resp = requests.get(
    f"{SUPABASE_CONFIG['url']}/rest/v1/dramas?select=flickreels_id",
    headers={"apikey": SUPABASE_CONFIG["key"]}
)
existing_ids = set(str(d['flickreels_id']) for d in resp.json() if d.get('flickreels_id'))

api = IndonesianAPI()
alive = []
dead = []
already_have = []

for i, d in enumerate(dramas):
    drama_id = str(d['id'])
    title = d['title']
    
    if drama_id in existing_ids:
        already_have.append(d)
        logger.info(f"  [{i+1}/{len(dramas)}] ⏭️ {title} — sudah di Supabase")
        continue
    
    # Test: get first episode's stream URL
    detail = api.get_drama_detail(drama_id)
    if not detail or not detail.get('episodes'):
        dead.append((d, "No detail/episodes"))
        logger.info(f"  [{i+1}/{len(dramas)}] 💀 {title} — no detail")
        continue
    
    # Try to play first episode
    first_ep = detail['episodes'][0]
    body = {**INDONESIAN_BODY, 'playlet_id': drama_id, 'chapter_id': str(first_ep['chapter_id'])}
    ts = str(int(time.time()))
    n = generate_nonce()
    s = generate_sign(body, ts, n)
    headers = {
        'token': FLICKREELS_CONFIG['token'],
        'sign': s, 'timestamp': ts, 'nonce': n,
        'version': FLICKREELS_CONFIG['version'],
        'content-type': 'application/json'
    }
    
    try:
        rate_limiter.acquire()
        r = requests.post(f"{FLICKREELS_CONFIG['base_url']}/app/playlet/play", json=body, headers=headers, timeout=15)
        result = r.json()
        
        if result.get('status_code') == 1:
            hls = result.get('data', {}).get('hls_url') or result.get('data', {}).get('hls')
            if hls:
                alive.append(d)
                logger.info(f"  [{i+1}/{len(dramas)}] ✅ {title} — ALIVE ({len(detail['episodes'])} eps)")
            else:
                dead.append((d, "No HLS URL in response"))
                logger.info(f"  [{i+1}/{len(dramas)}] 💀 {title} — no HLS URL")
        else:
            msg = result.get('msg', 'unknown')
            dead.append((d, msg))
            logger.info(f"  [{i+1}/{len(dramas)}] 💀 {title} — {msg}")
    except Exception as e:
        dead.append((d, str(e)))
        logger.info(f"  [{i+1}/{len(dramas)}] ❌ {title} — error: {e}")
    
    time.sleep(0.5)

# Report
logger.info(f"\n{'='*60}")
logger.info(f"PRE-CHECK RESULT")
logger.info(f"{'='*60}")
logger.info(f"  ✅ ALIVE (bisa scrape):     {len(alive)}")
logger.info(f"  💀 DEAD (dihapus/error):     {len(dead)}")
logger.info(f"  ⏭️ Already in Supabase:      {len(already_have)}")
logger.info(f"  Total:                       {len(dramas)}")

if dead:
    logger.info(f"\n  Dead dramas:")
    for d, reason in dead:
        logger.info(f"    💀 [{d['id']}] {d['title'][:40]} — {reason[:40]}")

# Save clean list (only alive)
if alive:
    with open('new_indonesian_alive.json', 'w', encoding='utf-8') as f:
        json.dump(alive, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✅ Saved {len(alive)} alive dramas to new_indonesian_alive.json")

logger.info(f"{'='*60}")
