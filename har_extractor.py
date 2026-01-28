"""
FlickReels HAR Data Extractor
=============================
Script ini mengekstrak data langsung dari file HAR yang sudah di-capture.
Ini berguna untuk melihat struktur data tanpa perlu mengakses API secara langsung.

Untuk scraping live, diperlukan:
1. Frida hook untuk capture sign secara real-time, atau
2. Decompile APK untuk mendapatkan secret key
"""

import json
from typing import List, Dict, Any

HAR_FILE = "API/1.har"

def load_har():
    """Load HAR file."""
    with open(HAR_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_entries_by_endpoint(har: dict, endpoint: str) -> List[dict]:
    """Get all entries matching an endpoint."""
    return [
        e for e in har['log']['entries'] 
        if endpoint in e['request']['url']
    ]

def extract_response_data(entry: dict) -> dict:
    """Extract JSON response from an entry."""
    text = entry['response']['content'].get('text', '')
    if text:
        try:
            return json.loads(text)
        except:
            return {}
    return {}

def extract_request_body(entry: dict) -> dict:
    """Extract request body from an entry."""
    if 'postData' in entry['request']:
        text = entry['request']['postData'].get('text', '')
        if text:
            try:
                return json.loads(text)
            except:
                return {}
    return {}

# ==============================================================================
# DATA EXTRACTION FUNCTIONS
# ==============================================================================

def get_all_dramas_from_har() -> List[Dict[str, Any]]:
    """
    Ekstrak semua drama dari HAR file (dari endpoint hotRank).
    
    Returns:
        List of drama objects dengan fields:
        - playlet_id, title, cover_url, description, chapter_total, dll
    """
    har = load_har()
    entries = get_entries_by_endpoint(har, '/app/playlet/hotRank')
    
    dramas = []
    for entry in entries:
        data = extract_response_data(entry)
        if data.get('status_code') == 1:
            for rank_group in data.get('data', []):
                for item in rank_group.get('data', []):
                    dramas.append({
                        "playlet_id": item.get("playlet_id"),
                        "title": item.get("title"),
                        "cover_url": item.get("cover_url"),
                        "description": item.get("description"),
                        "chapter_total": item.get("chapter_total"),
                        "collection_num": item.get("collection_num"),
                        "rank_order": item.get("rank_order"),
                        "rank_name": rank_group.get("name")
                    })
    
    # Deduplicate by playlet_id
    seen = set()
    unique_dramas = []
    for d in dramas:
        if d['playlet_id'] not in seen:
            seen.add(d['playlet_id'])
            unique_dramas.append(d)
    
    return unique_dramas

def get_all_episodes_from_har() -> Dict[str, List[Dict[str, Any]]]:
    """
    Ekstrak semua episode dari HAR file (dari endpoint chapterList).
    
    Returns:
        Dictionary dengan playlet_id sebagai key dan list episodes sebagai value
    """
    har = load_har()
    entries = get_entries_by_endpoint(har, '/app/playlet/chapterList')
    
    episodes_by_drama = {}
    
    for entry in entries:
        req_body = extract_request_body(entry)
        playlet_id = req_body.get('playlet_id')
        
        resp_data = extract_response_data(entry)
        if resp_data.get('status_code') == 1 and playlet_id:
            # Data is a dict with 'list' key containing episodes
            data = resp_data.get('data', {})
            episode_list = data.get('list', []) if isinstance(data, dict) else []
            
            episodes = []
            for ep in episode_list:
                if isinstance(ep, dict):
                    episodes.append({
                        "chapter_id": ep.get("chapter_id"),
                        "title": ep.get("title"),
                        "chapter_number": ep.get("chapter_num"),  # Note: 'chapter_num' not 'chapter_number'
                        "duration": ep.get("duration"),
                        "is_free": ep.get("is_free"),
                        "is_vip": ep.get("is_vip"),
                        "is_need_pay": ep.get("is_need_pay"),
                        "cover_url": ep.get("chapter_cover"),  # Note: 'chapter_cover' not 'cover_url'
                        "cost_coin": ep.get("cost_coin")
                    })
            
            if playlet_id not in episodes_by_drama:
                episodes_by_drama[playlet_id] = []
            episodes_by_drama[playlet_id].extend(episodes)
    
    return episodes_by_drama

def get_all_stream_urls_from_har() -> List[Dict[str, Any]]:
    """
    Ekstrak semua stream URL dari HAR file (dari endpoint play).
    
    Returns:
        List of stream info dengan fields:
        - playlet_id, chapter_id, hls (m3u8 URL), title, duration
    """
    har = load_har()
    entries = get_entries_by_endpoint(har, '/app/playlet/play')
    
    streams = []
    
    for entry in entries:
        # Skip playCheck and playLimit endpoints
        if 'playCheck' in entry['request']['url'] or 'playLimit' in entry['request']['url']:
            continue
        
        req_body = extract_request_body(entry)
        data = extract_response_data(entry)
        
        if data.get('status_code') == 1:
            play_data = data.get('data', {})
            if play_data.get('hls'):
                streams.append({
                    "playlet_id": req_body.get("playlet_id"),
                    "chapter_id": req_body.get("chapter_id"),
                    "title": play_data.get("title"),
                    "hls": play_data.get("hls"),
                    "duration": play_data.get("total_duration"),
                    "is_free": play_data.get("is_need_pay") == 0,
                    "hls_timeout": play_data.get("hls_timeout"),
                    "tags": [t.get("tag_name") for t in play_data.get("tag_list", [])]
                })
    
    return streams

def get_captured_headers(endpoint: str) -> Dict[str, str]:
    """
    Ekstrak headers yang digunakan untuk endpoint tertentu.
    Berguna untuk melihat struktur header yang diperlukan.
    """
    har = load_har()
    entries = get_entries_by_endpoint(har, endpoint)
    
    if entries:
        return {h['name']: h['value'] for h in entries[0]['request']['headers']}
    return {}

def export_to_json(data: Any, filename: str):
    """Export data ke file JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Data exported to {filename}")

# ==============================================================================
# MAIN - Demo
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FlickReels HAR Data Extractor")
    print("=" * 60)
    
    # 1. Extract all dramas
    print("\n[1] Extracting dramas from HAR...")
    dramas = get_all_dramas_from_har()
    print(f"    Found {len(dramas)} unique dramas")
    
    if dramas:
        print("\n    Sample dramas:")
        for i, d in enumerate(dramas[:5]):
            print(f"    {i+1}. [{d['playlet_id']}] {d['title']}")
            print(f"       Episodes: {d['chapter_total']} | Rank: {d['rank_name']}")
    
    # 2. Extract all episodes
    print("\n[2] Extracting episodes from HAR...")
    episodes = get_all_episodes_from_har()
    total_eps = sum(len(eps) for eps in episodes.values())
    print(f"    Found {total_eps} episodes across {len(episodes)} dramas")
    
    for pid, eps in list(episodes.items())[:2]:
        print(f"\n    Drama {pid}:")
        for ep in eps[:3]:
            print(f"      EP.{ep['chapter_number']}: [{ep['chapter_id']}] {ep['title']} ({ep['duration']}s)")
    
    # 3. Extract stream URLs
    print("\n[3] Extracting stream URLs from HAR...")
    streams = get_all_stream_urls_from_har()
    print(f"    Found {len(streams)} stream URLs")
    
    if streams:
        print("\n    Sample streams:")
        for s in streams[:3]:
            print(f"    [{s['playlet_id']}/{s['chapter_id']}] {s['title']}")
            print(f"      Duration: {s['duration']}s | Free: {s['is_free']}")
            print(f"      URL: {s['hls'][:80]}...")
            print(f"      Tags: {', '.join(s['tags'][:5])}")
            print()
    
    # 4. Show sample headers
    print("\n[4] Sample request headers (from /app/playlet/play):")
    headers = get_captured_headers('/app/playlet/play')
    important = ['version', 'sign', 'timestamp', 'nonce', 'token']
    for h in important:
        val = headers.get(h, 'N/A')
        if len(val) > 60:
            print(f"    {h}: {val[:60]}...")
        else:
            print(f"    {h}: {val}")
    
    # 5. Export data
    print("\n[5] Exporting data to JSON files...")
    export_to_json(dramas, "extracted_dramas.json")
    export_to_json(episodes, "extracted_episodes.json")
    export_to_json(streams, "extracted_streams.json")
    
    print("\n" + "=" * 60)
    print("Extraction complete!")
    print("=" * 60)
    print("\n💡 Tips:")
    print("   - Stream URLs have verify tokens that expire (check hls_timeout)")
    print("   - For live scraping, you need to capture fresh headers")
    print("   - Use HTTP Toolkit to capture new requests from the app")
