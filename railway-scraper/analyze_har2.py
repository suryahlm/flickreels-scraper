#!/usr/bin/env python3
"""
HAR File Analyzer - Clean version
"""
import json
import sys
from collections import defaultdict
from urllib.parse import urlparse

def analyze_har_simple(har_path):
    """Simple analysis focusing on unique endpoints"""
    
    with open(har_path, 'r', encoding='utf-8', errors='replace') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    filename = har_path.split('\\')[-1]
    print(f"\n=== {filename} ({len(entries)} entries) ===")
    
    # Collect all unique endpoints with their params
    endpoint_data = defaultdict(list)
    
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        url = request.get('url', '')
        
        if 'farsunpteltd.com/app/' not in url:
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
        resp_data = {}
        if resp_text:
            try:
                resp_data = json.loads(resp_text)
            except:
                pass
        
        endpoint_data[path].append({
            'body': body,
            'response': resp_data
        })
    
    # Print unique endpoints
    print(f"Unique API endpoints: {len(endpoint_data)}")
    
    for path in sorted(endpoint_data.keys()):
        calls = endpoint_data[path]
        print(f"\n{path} ({len(calls)}x)")
        
        for i, call in enumerate(calls[:2]):  # First 2 calls only
            body = call['body']
            resp = call['response']
            
            # Important params
            params = []
            for key in ['page', 'page_size', 'navigation_id', 'language_id', 'playlet_id', 'column_config_id']:
                if key in body:
                    params.append(f"{key}={body[key]}")
            
            if params:
                print(f"  [{i+1}] {', '.join(params)}")
            
            # Response info
            if resp.get('status_code') == 1:
                data = resp.get('data', {})
                if isinstance(data, list):
                    total = 0
                    for section in data:
                        if isinstance(section, dict) and 'list' in section:
                            total += len(section['list'])
                    if total > 0:
                        print(f"      -> {total} items")
                elif isinstance(data, dict):
                    if 'list' in data:
                        print(f"      -> {len(data['list'])} items in list")

def main():
    files = [
        r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 1.har",
        r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 2.har"
    ]
    
    for f in files:
        try:
            analyze_har_simple(f)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
