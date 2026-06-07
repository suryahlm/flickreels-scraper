#!/usr/bin/env python3
"""
Quick test of drama discovery
"""
import sys
sys.path.insert(0, '.')
from batch_scraper_indonesia import IndonesianAPI

api = IndonesianAPI()

# Test both methods
print("Testing navigationColumn...")
dramas1 = api.get_indonesian_dramas(page=1)
print(f"  Page 1: {len(dramas1)} dramas")

print("\nTesting lastColumn (config=11274)...")
dramas2 = api.get_indonesian_dramas_lastcolumn(page=1, column_config_id="11274")
print(f"  Page 1: {len(dramas2)} dramas")

print("\nTesting lastColumn (config=6826)...")
dramas3 = api.get_indonesian_dramas_lastcolumn(page=1, column_config_id="6826", nav_id="78")
print(f"  Page 1: {len(dramas3)} dramas")

# Count total unique
all_ids = set()
for d in dramas1 + dramas2 + dramas3:
    all_ids.add(d['id'])
print(f"\nTotal unique from all 3 calls: {len(all_ids)}")
