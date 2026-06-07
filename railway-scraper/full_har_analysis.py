#!/usr/bin/env python3
"""
Complete analysis of all API endpoints in HAR files
"""
import json
from collections import defaultdict
from urllib.parse import urlparse

def full_analysis(har_path):
    with open(har_path, 'r', encoding='utf-8', errors='replace') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    filename = har_path.split('\\')[-1]
    
    print(f"\n{'='*70}")
    print(f"FILE: {filename}")
    print(f"{'='*70}")
    
    # Collect ALL endpoints
    endpoints = defaultdict(list)
    
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        if 'farsunpteltd.com' not in url:
            continue
        
        parsed = urlparse(url)
        path = parsed.path
        
        # Get request body
        post_data = request.get('postData', {})
        body_text = post_data.get('text', '')
        body = {}
        if body_text:
            try:
                body = json.loads(body_text)
            except:
                pass
        
        # Get response
        content = response.get('content', {})
        resp_text = content.get('text', '')
        resp = {}
        if resp_text:
            try:
                resp = json.loads(resp_text)
            except:
                pass
        
        endpoints[path].append({
            'body': body,
            'response': resp
        })
    
    # Print only /app/ endpoints with details
    for path in sorted(endpoints.keys()):
        if '/app/' not in path:
            continue
            
        calls = endpoints[path]
        print(f"\n{path} ({len(calls)}x)")
        
        # Show all unique body params across calls
        all_params = set()
        for call in calls:
            all_params.update(call['body'].keys())
        
        # Filter out device params
        skip = ['main_package_id', 'googleAdId', 'device_id', 'device_sign',
                'apps_flyer_uid', 'os', 'device_brand', 'device_number', 
                'device_model', 'countryCode', 'language_id']
        important = [p for p in all_params if p not in skip]
        
        if important:
            print(f"  Params: {sorted(important)}")
        
        # Show response data structure
        for i, call in enumerate(calls[:1]):  # First call only
            resp = call['response']
            if resp.get('status_code') == 1:
                data = resp.get('data')
                if data:
                    if isinstance(data, list):
                        if len(data) > 0 and isinstance(data[0], dict):
                            print(f"  Response: list[{len(data)}] with keys: {list(data[0].keys())[:5]}")
                    elif isinstance(data, dict):
                        print(f"  Response: dict with keys: {list(data.keys())[:8]}")

files = [
    r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 1.har",
    r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 2.har"
]

for f in files:
    full_analysis(f)
