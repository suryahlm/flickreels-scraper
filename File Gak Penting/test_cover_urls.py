#!/usr/bin/env python3
"""Test cover URL encoding issues."""
import requests
from urllib.parse import quote

base = "https://tender-connection-production-246f.up.railway.app"

# Get first drama from API
r = requests.get(f"{base}/api/r2-dramas", timeout=60)
data = r.json()
dramas = data.get("dramas", [])

print("Testing first 5 cover URLs:\n")

for d in dramas[:5]:
    title = d.get("title", "")
    folder = d.get("folder_name", "")
    cover_url = d.get("cover_url", "")
    
    print(f"Title: {title}")
    print(f"Folder: {folder}")
    print(f"Cover URL: {cover_url}")
    
    # Test the cover URL
    try:
        cr = requests.head(cover_url, timeout=10, allow_redirects=True)
        print(f"Status: {cr.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Try with different encoding
    alt_url = f"{base}/api/stream/flickreels/{quote(folder, safe='()')}/cover.jpg"
    print(f"Alt URL: {alt_url}")
    try:
        cr = requests.head(alt_url, timeout=10, allow_redirects=True)
        print(f"Alt Status: {cr.status_code}")
    except Exception as e:
        print(f"Alt Error: {e}")
    
    print("-" * 60)
