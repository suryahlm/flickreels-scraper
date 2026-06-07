#!/usr/bin/env python3
"""
Extract all unique column_config_ids from HAR files
"""
import json
from collections import defaultdict

def extract_column_configs(har_path):
    with open(har_path, 'r', encoding='utf-8', errors='replace') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    configs = defaultdict(set)
    
    for entry in entries:
        request = entry.get('request', {})
        url = request.get('url', '')
        
        if 'farsunpteltd.com/app/' not in url:
            continue
            
        post_data = request.get('postData', {})
        body_text = post_data.get('text', '')
        
        if body_text:
            try:
                body = json.loads(body_text)
                config_id = body.get('column_config_id')
                nav_id = body.get('navigation_id')
                
                if config_id:
                    configs[nav_id].add(str(config_id))
            except:
                pass
    
    return configs

files = [
    r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 1.har",
    r"D:\Surya\IT\AsianDrama-02\FlickReels\API\scroll_browse 2.har"
]

all_configs = defaultdict(set)

for f in files:
    configs = extract_column_configs(f)
    for nav, cfgs in configs.items():
        all_configs[nav].update(cfgs)

print("Column Config IDs by Navigation ID:")
print("="*50)
for nav, cfgs in sorted(all_configs.items(), key=lambda x: str(x[0])):
    print(f"Navigation {nav}: {sorted(cfgs)}")
