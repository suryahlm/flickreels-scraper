#!/usr/bin/env python3
"""Count unique IDs in ID 6.txt"""
import re

with open(r'D:\Surya\IT\AsianDrama-02\FlickReels\API\ID 6.txt', encoding='utf-8') as f:
    content = f.read()

ids = set(re.findall(r'"playlet_id":\s*(\d+)', content))
print(f'Unique playlet_ids in ID 6.txt: {len(ids)}')
print(f'Sample IDs: {list(ids)[:10]}')
