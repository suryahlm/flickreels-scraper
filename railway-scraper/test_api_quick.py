#!/usr/bin/env python3
"""Quick test of the Indonesian API"""
import sys
sys.path.insert(0, '.')
from batch_scraper_indonesia import IndonesianAPI

api = IndonesianAPI()
dramas = api.get_indonesian_dramas(page=1)
print(f'Found {len(dramas)} dramas on page 1')
if dramas:
    for d in dramas[:5]:
        print(f"  - {d['id']}: {d['title'][:50]}")
