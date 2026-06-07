#!/usr/bin/env python3
"""
CRACK CONTENT NEGOTIATION
==========================
Test semua hipotesis untuk mendapatkan judul/metadata Indonesia dari API.

Hipotesis:
A. Endpoint alternatif (introduce, detail, info)
B. Header injection (Accept-Language, lang, language)
C. Perbandingan video URL (language_id 6 vs 1)
D. Body param alternatif (lang, locale)
"""
import sys
sys.path.insert(0, '.')
import json
import time
import requests
import copy
from local_scraping_indonesia import (
    generate_sign, generate_nonce,
    FLICKREELS_CONFIG, INDONESIAN_BODY,
    rate_limiter
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Test dengan drama ID 14 ("My Powerful Queen" dalam English)
TEST_ID = "14"
TEST_CHAPTER_ID = None  # Will be filled from chapterList


def api_request(endpoint, body_override=None, extra_headers=None):
    body = body_override or {**INDONESIAN_BODY}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    
    headers = {
        "token": FLICKREELS_CONFIG["token"],
        "sign": sign,
        "timestamp": timestamp,
        "nonce": nonce,
        "version": FLICKREELS_CONFIG["version"],
        "content-type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    
    try:
        rate_limiter.acquire()
        resp = requests.post(
            f"{FLICKREELS_CONFIG['base_url']}{endpoint}",
            json=body, headers=headers, timeout=15
        )
        return resp.json()
    except Exception as e:
        return {"status_code": -1, "msg": str(e)}


# ============================================================
# HIPOTESIS A: Endpoint Alternatif
# ============================================================
print("=" * 70)
print("HIPOTESIS A: Endpoint Alternatif (Metadata Lokalisasi)")
print("=" * 70)

# Pertama ambil baseline dari chapterList
baseline = api_request("/app/playlet/chapterList", {**INDONESIAN_BODY, "playlet_id": TEST_ID})
if baseline.get("status_code") == 1:
    data = baseline["data"]
    print(f"\n  BASELINE (chapterList, language_id=6):")
    print(f"    title: {data.get('title')}")
    print(f"    language_name: '{data.get('language_name')}'")
    print(f"    keys: {list(data.keys())}")
    
    # Get first chapter ID for play endpoint test
    episodes = data.get("list", [])
    if episodes:
        TEST_CHAPTER_ID = str(episodes[0].get("chapter_id", ""))
        print(f"    First chapter ID: {TEST_CHAPTER_ID}")

# Test alternative endpoints
alt_endpoints = [
    "/app/playlet/introduce",
    "/app/playlet/detail",
    "/app/playlet/info",
    "/app/playlet/getDetail",
    "/app/playlet/getInfo",
    "/app/playlet/playletInfo",
    "/app/playlet/playletDetail",
    "/app/drama/detail",
    "/app/drama/info",
]

for ep in alt_endpoints:
    body = {**INDONESIAN_BODY, "playlet_id": TEST_ID}
    result = api_request(ep, body)
    status = result.get("status_code")
    msg = str(result.get("msg", ""))[:60]
    
    if status == 1:
        data = result.get("data", {})
        title = data.get("title", "") if isinstance(data, dict) else ""
        print(f"\n  ✅ {ep}")
        print(f"     title: {title}")
        if isinstance(data, dict):
            print(f"     keys: {list(data.keys())[:10]}")
    else:
        print(f"  ❌ {ep}: {msg}")
    time.sleep(0.3)


# ============================================================
# HIPOTESIS B: Header Injection
# ============================================================
print(f"\n{'=' * 70}")
print("HIPOTESIS B: Header Injection (Accept-Language, lang, dll)")
print("=" * 70)

header_combos = [
    {"Accept-Language": "id-ID,id;q=0.9"},
    {"Accept-Language": "id"},
    {"lang": "id"},
    {"language": "id"},
    {"locale": "id_ID"},
    {"lang": "id", "Accept-Language": "id-ID,id;q=0.9"},
    {"lang": "id", "language": "id", "Accept-Language": "id-ID,id;q=0.9", "locale": "id_ID"},
    {"X-Language": "id"},
    {"X-Lang": "id"},
    {"X-Locale": "id-ID"},
]

for combo in header_combos:
    body = {**INDONESIAN_BODY, "playlet_id": TEST_ID}
    result = api_request("/app/playlet/chapterList", body, extra_headers=combo)
    
    if result.get("status_code") == 1:
        title = result["data"].get("title", "")
        lang = result["data"].get("language_name", "")
        header_str = ", ".join(f"{k}={v}" for k, v in combo.items())
        changed = "🔥 CHANGED!" if title != "My Powerful Queen" else "same"
        print(f"  [{changed}] Headers: {header_str}")
        print(f"         title: {title} | lang: '{lang}'")
    time.sleep(0.3)


# ============================================================
# HIPOTESIS C: Body Param Alternatif
# ============================================================
print(f"\n{'=' * 70}")
print("HIPOTESIS C: Body Param Alternatif")
print("=" * 70)

param_combos = [
    {"lang": "id"},
    {"lang": "id_ID"},
    {"locale": "id_ID"},
    {"locale": "id"},
    {"language": "id"},
    {"language": "indonesian"},
    {"language_code": "id"},
    {"language_id": 6},           # As integer instead of string
    {"language_id": "6", "lang": "id"},
    {"language_id": "6", "locale": "id_ID", "lang": "id"},
]

for combo in param_combos:
    body = {**INDONESIAN_BODY, "playlet_id": TEST_ID, **combo}
    result = api_request("/app/playlet/chapterList", body)
    
    if result.get("status_code") == 1:
        title = result["data"].get("title", "")
        lang = result["data"].get("language_name", "")
        param_str = ", ".join(f"{k}={v}" for k, v in combo.items())
        changed = "🔥 CHANGED!" if title != "My Powerful Queen" else "same"
        print(f"  [{changed}] Params: {param_str}")
        print(f"         title: {title} | lang: '{lang}'")
    time.sleep(0.3)


# ============================================================
# HIPOTESIS D: Perbandingan Video URL (language_id 6 vs 1)
# ============================================================
print(f"\n{'=' * 70}")
print("HIPOTESIS D: Perbandingan Video URL (/play)")
print("=" * 70)

if TEST_CHAPTER_ID:
    # Request with language_id = 6 (Indonesian)
    body_indo = {**INDONESIAN_BODY, "chapter_id": TEST_CHAPTER_ID}
    result_indo = api_request("/app/playlet/play", body_indo)
    
    # Request with language_id = 1 (English, assumed)
    body_en = {**INDONESIAN_BODY, "chapter_id": TEST_CHAPTER_ID}
    body_en["language_id"] = "1"
    result_en = api_request("/app/playlet/play", body_en)
    
    # Request with language_id = 0 (default?)
    body_0 = {**INDONESIAN_BODY, "chapter_id": TEST_CHAPTER_ID}
    body_0["language_id"] = "0"
    result_0 = api_request("/app/playlet/play", body_0)
    
    print(f"\n  Chapter ID: {TEST_CHAPTER_ID}")
    
    for label, result in [("language_id=6 (Indo)", result_indo), 
                           ("language_id=1 (EN?)", result_en),
                           ("language_id=0 (Def?)", result_0)]:
        if result.get("status_code") == 1:
            data = result.get("data", {})
            if isinstance(data, dict):
                url = data.get("play_url", data.get("url", data.get("filepath", "")))
                print(f"\n  [{label}]")
                print(f"    URL: {url[:120]}...")
                print(f"    Keys: {list(data.keys())[:10]}")
            elif isinstance(data, str):
                print(f"\n  [{label}]")
                print(f"    Data (string): {data[:120]}...")
        else:
            print(f"\n  [{label}] ❌ {result.get('msg', '')[:60]}")
else:
    print("  ⚠️ No chapter ID available to test")


# ============================================================
# HIPOTESIS E: Cek navigationColumn title vs chapterList title
# ============================================================
print(f"\n{'=' * 70}")
print("HIPOTESIS E: Bandingkan Judul dari Nav Feed vs ChapterList")
print("=" * 70)

# Get drama from nav_id=30 (Indonesian feed)
nav_result = api_request("/app/playlet/navigationColumn", {
    **INDONESIAN_BODY, "navigation_id": "30", "page": 1, "page_size": 5
})
if nav_result.get("status_code") == 1:
    nav_data = nav_result.get("data", [])
    for section in nav_data:
        for item in section.get("list", [])[:3]:
            nav_title = item.get("title", "")
            nav_id = str(item.get("playlet_id", ""))
            
            # Now get same drama from chapterList
            detail = api_request("/app/playlet/chapterList", {
                **INDONESIAN_BODY, "playlet_id": nav_id
            })
            if detail.get("status_code") == 1:
                cl_title = detail["data"].get("title", "")
                same = "✅ SAMA" if nav_title == cl_title else "⚠️ BEDA!"
                print(f"  ID {nav_id}:")
                print(f"    Nav title:         {nav_title}")
                print(f"    ChapterList title: {cl_title}")
                print(f"    {same}")
            time.sleep(0.3)


# ============================================================
# HIPOTESIS F: Cek drama English dari nav_id=1 dengan language_id=6
# ============================================================
print(f"\n{'=' * 70}")
print("HIPOTESIS F: Drama English (nav_id=1) vs Indonesian request")
print("=" * 70)

# Get dramas from English nav
nav_en = api_request("/app/playlet/navigationColumn", {
    **INDONESIAN_BODY, "navigation_id": "1", "page": 1, "page_size": 5
})
if nav_en.get("status_code") == 1:
    for section in nav_en.get("data", []):
        for item in section.get("list", [])[:3]:
            en_title = item.get("title", "")
            en_id = str(item.get("playlet_id", ""))
            
            # Get Indonesian version
            detail_indo = api_request("/app/playlet/chapterList", {
                **INDONESIAN_BODY, "playlet_id": en_id
            })
            if detail_indo.get("status_code") == 1:
                indo_title = detail_indo["data"].get("title", "")
                same = "SAMA" if en_title == indo_title else "🔥 BEDA!"
                print(f"  ID {en_id}:")
                print(f"    Nav (EN) title:    {en_title[:50]}")
                print(f"    ChapterList title: {indo_title[:50]}")
                print(f"    [{same}]")
            time.sleep(0.3)


print(f"\n{'=' * 70}")
print("SELESAI - Review hasil di atas untuk strategi selanjutnya")
print(f"{'=' * 70}")
