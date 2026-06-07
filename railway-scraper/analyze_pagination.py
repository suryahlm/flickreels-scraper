#!/usr/bin/env python3
"""
HAR File Analyzer - Focus on scroll_browse 2.har for pagination endpoints
"""
import json
from collections import defaultdict
from urllib.parse import urlparse

def analyze_har(har_path):
    with open(har_path, 'r', encoding='utf-8', errors='replace') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    
    # Focus on endpoints with pagination
    pagination_endpoints = []
    
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
        
        if body_text:
            try:
                body = json.loads(body_text)
                page = body.get('page')
                if page and int(page) > 1:  # Pagination!
                    pagination_endpoints.append({
                        'path': path,
                        'page': page,
                        'page_size': body.get('page_size'),
                        'navigation_id': body.get('navigation_id'),
                        'column_config_id': body.get('column_config_id'),
                        'language_id': body.get('language_id'),
                        'full_body': body
                    })
            except:
                pass
    
    print("=== PAGINATION ENDPOINTS (page > 1) ===\n")
    
    if not pagination_endpoints:
        print("No pagination endpoints found!")
    else:
        for ep in pagination_endpoints:
            print(f"Endpoint: {ep['path']}")
            print(f"  page: {ep['page']}")
            print(f"  page_size: {ep['page_size']}")
            print(f"  navigation_id: {ep['navigation_id']}")
            print(f"  column_config_id: {ep['column_config_id']}")
            print(f"  language_id: {ep['language_id']}")
            print()

# Analyze file 2
analyze_har(r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 2.har")
