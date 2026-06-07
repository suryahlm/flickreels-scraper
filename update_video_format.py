#!/usr/bin/env python3
"""Update video_format to 'mp4' in Supabase for converted dramas."""
import requests
import json

SUPABASE_URL = "https://bmryonqbddbkjbtquhgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# FlickReels IDs for the 2 converted dramas
converted_ids = ["2234", "4509"]

for fid in converted_ids:
    # Get current data
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{fid}&select=id,title,flickreels_id,source_data,r2_folder",
        headers=headers
    )
    
    if resp.status_code == 200 and resp.json():
        drama = resp.json()[0]
        title = drama.get("title", "Unknown")
        r2_folder = drama.get("r2_folder", "N/A")
        print(f"Found: {title} (fid={fid})")
        print(f"  r2_folder: {r2_folder}")
        
        current_source = drama.get("source_data") or {}
        current_format = current_source.get("video_format", "not set")
        print(f"  current video_format: {current_format}")
        
        # Update source_data to include video_format: mp4
        current_source["video_format"] = "mp4"
        
        update_resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{fid}",
            headers=headers,
            json={"source_data": current_source}
        )
        
        if update_resp.status_code in [200, 204]:
            print(f"  ✅ Updated video_format to 'mp4'!")
        else:
            print(f"  ❌ Update failed: {update_resp.status_code}")
            print(f"     {update_resp.text[:200]}")
    else:
        print(f"❌ Drama fid={fid} not found: {resp.status_code}")
    
    print()

print("Done!")
