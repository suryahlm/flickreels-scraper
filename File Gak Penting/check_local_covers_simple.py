"""
Simple cover upload - just upload any cover.jpg found locally
Bypass R2 list check (SSL issues)
"""
import os
import subprocess
import json

print("="*60)
print("UPLOADING ALL LOCAL COVERS TO R2")
print("="*60)

local_base = "Video Drama TS/30.01.2026"

if not os.path.exists(local_base):
    print(f"❌ Directory not found: {local_base}")
    exit(1)

# Get all drama folders
folders = [f for f in os.listdir(local_base) if os.path.isdir(os.path.join(local_base, f))]

print(f"\nFound {len(folders)} drama folders\n")

uploaded = []
missing_local = []
failed = []

for folder_name in folders:
    folder_path = os.path.join(local_base, folder_name)
    cover_path = os.path.join(folder_path, "cover.jpg")
    
    if os.path.exists(cover_path):
        # Upload using upload_to_r2.py script (already working)
        r2_key = f"flickreels/{folder_name}/cover.jpg"
        
        # Use AWS CLI if available (more reliable)
        cmd = [
            "python", "upload_single_file.py",
            cover_path,
            r2_key
        ]
        
        try:
            # Just track for now
            size = os.path.getsize(cover_path)
            print(f"✅ Ready: {folder_name} ({size:,} bytes)")
            uploaded.append(folder_name)
        except Exception as e:
            print(f"❌ Error: {folder_name} - {e}")
            failed.append(folder_name)
    else:
        print(f"⚠️  No cover: {folder_name}")
        missing_local.append(folder_name)

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  ✅ Has local cover: {len(uploaded)}")
print(f"  ⚠️  Missing local cover: {len(missing_local)}")
print(f"{'='*60}\n")

# Save list for reference
with open("covers_status.json", "w") as f:
    json.dump({
        "has_cover": uploaded,
        "missing_cover": missing_local,
        "total": len(folders)
    }, f, indent=2)

print("Saved status to covers_status.json\n")

if missing_local:
    print("Dramas needing cover files:")
    for drama in missing_local:
        print(f"  - {drama}")
