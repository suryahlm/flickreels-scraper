#!/usr/bin/env python3
"""
Compare discovered dramas with Supabase database
"""
import json
import requests

SUPABASE_URL = "https://dybsitvwxgzkluyydquk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR5YnNpdHZ3eGd6a2x1eXlkcXVrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc4NzY5MjAsImV4cCI6MjA1MzQ1MjkyMH0.4anGVW0zxFN8J0kTDSSmZdGSrAG1xejpQGV2v6T0oCQ"

# Get discovered dramas
with open("comprehensive_dramas.json", "r", encoding="utf-8") as f:
    discovered = json.load(f)

discovered_ids = set(str(d['id']) for d in discovered)
print(f"Discovered dramas: {len(discovered_ids)}")

# Get existing dramas from Supabase
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/dramas?select=flickreels_id",
    headers={"apikey": SUPABASE_KEY}
)

existing = resp.json()
existing_ids = set(str(d['flickreels_id']) for d in existing if d.get('flickreels_id'))
print(f"Existing in DB: {len(existing_ids)}")

# Find new dramas
new_ids = discovered_ids - existing_ids
print(f"\nNEW dramas to scrape: {len(new_ids)}")

# Find dramas in DB but not discovered (maybe removed from API)
orphan_ids = existing_ids - discovered_ids
print(f"In DB but not in API: {len(orphan_ids)}")

# Show new drama titles
if new_ids:
    print("\nNew dramas:")
    for drama in discovered:
        if str(drama['id']) in new_ids:
            print(f"  {drama['id']}: {drama.get('title', 'N/A')[:50]}")
    
    # Save new dramas
    new_dramas = [d for d in discovered if str(d['id']) in new_ids]
    with open("new_dramas_to_scrape.json", "w", encoding="utf-8") as f:
        json.dump(new_dramas, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to new_dramas_to_scrape.json")
