"""Fix Supabase video_format for dramas that failed during HLS→MP4 conversion."""
import requests

SUPABASE_URL = "https://bmryonqbddbkjbtquhgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# Find all FlickReels dramas where video_format is NOT mp4 (these are the ones that failed)
r = requests.get(
    f"{SUPABASE_URL}/rest/v1/dramas",
    params={
        "is_published": "eq.true",
        "select": "id,title,flickreels_id,source_data,r2_folder",
    },
    headers=headers,
    timeout=15,
)

data = r.json()

# Filter: FlickReels dramas (not dramabox, not melolo) where video_format != mp4
needs_fix = []
for d in data:
    sd = d.get("source_data") or {}
    folder = d.get("r2_folder", "")
    
    # Skip dramabox and melolo
    if folder.startswith("dramabox/") or folder.startswith("melolo/"):
        continue
    
    # Check if video_format is not mp4
    if sd.get("video_format") != "mp4":
        needs_fix.append(d)

print(f"Found {len(needs_fix)} dramas needing video_format fix:")
for d in needs_fix:
    sd = d.get("source_data") or {}
    print(f"  - [{d['flickreels_id']}] {d['title'][:50]} (current: {sd.get('video_format', 'N/A')})")

# Fix them
fixed = 0
for d in needs_fix:
    sd = d.get("source_data") or {}
    sd["video_format"] = "mp4"
    
    try:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/dramas?id=eq.{d['id']}",
            json={"source_data": sd},
            headers=headers,
            timeout=15,
        )
        if r.status_code in (200, 204):
            fixed += 1
            print(f"  ✅ Fixed: [{d['flickreels_id']}] {d['title'][:50]}")
        else:
            print(f"  ❌ Failed: [{d['flickreels_id']}] {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: [{d['flickreels_id']}] {str(e)[:80]}")

print(f"\nDone: {fixed}/{len(needs_fix)} fixed")
