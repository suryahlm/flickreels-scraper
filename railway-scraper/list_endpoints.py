#!/usr/bin/env python3
"""
Extract ALL unique endpoint paths from HAR
"""
import json
from urllib.parse import urlparse
from collections import Counter

def extract_endpoints(har_path):
    with open(har_path, 'r', encoding='utf-8', errors='replace') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    return har_path.split('\\')[-1], entries

endpoints = Counter()
all_entries = []

files = [
    r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 1.har",
    r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 2.har"
]

for f in files:
    name, entries = extract_endpoints(f)
    for entry in entries:
        url = entry.get('request', {}).get('url', '')
        if 'farsunpteltd.com' in url:
            path = urlparse(url).path
            endpoints[path] += 1
            all_entries.append((path, entry))

print("ALL API Endpoints called:")
print("="*60)
for path, count in endpoints.most_common():
    print(f"  {count:3}x  {path}")

print(f"\nTotal unique endpoints: {len(endpoints)}")
print(f"Total API calls: {sum(endpoints.values())}")
