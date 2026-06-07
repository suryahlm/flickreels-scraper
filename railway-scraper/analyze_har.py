#!/usr/bin/env python3
"""
HAR File Analyzer - Focus on API endpoints for drama discovery
"""
import json
import sys
from collections import defaultdict
from urllib.parse import urlparse

def analyze_har(har_path):
    """Analyze a HAR file and extract API information"""
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    print(f"\n{'='*70}")
    print(f"File: {har_path.split(chr(92))[-1]}")
    print(f"Total entries: {len(entries)}")
    print(f"{'='*70}")
    
    # Filter for API calls (not images/videos)
    api_calls = []
    for entry in entries:
        request = entry.get('request', {})
        url = request.get('url', '')
        if 'farsunpteltd.com/app/' in url:  # Only /app/ API endpoints
            api_calls.append(entry)
    
    print(f"API calls (excluding media): {len(api_calls)}\n")
    
    # Group by endpoint
    endpoints = defaultdict(list)
    for entry in api_calls:
        request = entry.get('request', {})
        url = request.get('url', '')
        parsed = urlparse(url)
        endpoints[parsed.path].append(entry)
    
    # Sort by endpoint
    for path in sorted(endpoints.keys()):
        calls = endpoints[path]
        print(f"\n{'='*70}")
        print(f"ENDPOINT: {path} ({len(calls)} calls)")
        print(f"{'='*70}")
        
        for i, entry in enumerate(calls):
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            # Parse request body
            post_data = request.get('postData', {})
            body_text = post_data.get('text', '')
            
            if body_text:
                try:
                    body = json.loads(body_text)
                    
                    print(f"\n  --- Call {i+1} ---")
                    print(f"  Request params:")
                    
                    # Important params
                    important = ['page', 'page_size', 'navigation_id', 'language_id', 
                                 'playlet_id', 'chapter_id', 'column_config_id', 'keyword']
                    for key in important:
                        if key in body:
                            print(f"    {key}: {body[key]}")
                    
                    # All other non-device params
                    skip = ['main_package_id', 'googleAdId', 'device_id', 'device_sign',
                            'apps_flyer_uid', 'os', 'device_brand', 'device_number', 
                            'device_model', 'countryCode'] + important
                    other = {k: v for k, v in body.items() if k not in skip}
                    if other:
                        for k, v in other.items():
                            if isinstance(v, (str, int, float, bool)):
                                print(f"    {k}: {v}")
                            else:
                                print(f"    {k}: {type(v).__name__}")
                    
                except json.JSONDecodeError:
                    pass
            
            # Check response
            content = response.get('content', {})
            resp_text = content.get('text', '')
            if resp_text:
                try:
                    resp = json.loads(resp_text)
                    status_code = resp.get('status_code', 'N/A')
                    msg = resp.get('msg', '')
                    data = resp.get('data', {})
                    
                    print(f"  Response:")
                    print(f"    status: {status_code} ({msg})")
                    
                    # Count items
                    if isinstance(data, list):
                        total_items = 0
                        for section in data:
                            if isinstance(section, dict) and 'list' in section:
                                items = section['list']
                                if items:
                                    total_items += len(items)
                                    # Show first item title
                                    first = items[0]
                                    if 'title' in first:
                                        print(f"    data: {len(items)} items (e.g. \"{first['title'][:30]}...\")")
                        if total_items == 0:
                            print(f"    data: list with {len(data)} sections")
                    elif isinstance(data, dict):
                        if 'list' in data:
                            items = data['list']
                            if items and len(items) > 0:
                                first = items[0]
                                if 'title' in first:
                                    print(f"    data.list: {len(items)} items (e.g. \"{first.get('title', '')[:30]}\")")
                                else:
                                    print(f"    data.list: {len(items)} items")
                        elif 'chapters' in data:
                            print(f"    data.chapters: {len(data['chapters'])} chapters")
                        elif 'title' in data:
                            print(f"    drama: \"{data['title'][:40]}\"")
                        else:
                            print(f"    data keys: {list(data.keys())[:5]}")
                    
                except json.JSONDecodeError:
                    pass

def main():
    har_files = [
        r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 1.har",
        r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 2.har"
    ]
    
    for har_file in har_files:
        try:
            analyze_har(har_file)
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
