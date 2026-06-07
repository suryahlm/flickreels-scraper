"""
Check if these 3 specific dramas have cover.jpg files
"""
import os
from pathlib import Path

dramas_to_check = [
    "Sayang, Aku Benaran Amnesia (3164)",
    "Kejayaanku Setelah Berpisah",
    "Istri Kesayangan Mafia"
]

base_path = Path("Video Drama TS/30.01.2026")

print("\n" + "="*60)
print("CHECKING SPECIFIC DRAMAS FOR COVER FILES")
print("="*60)

for drama_name in dramas_to_check:
    print(f"\n🔍 Checking: {drama_name}")
    
    # Try to find folder
    found = False
    for folder in base_path.iterdir():
        if folder.is_dir() and drama_name.lower() in folder.name.lower():
            found = True
            cover_path = folder / "cover.jpg"
            
            if cover_path.exists():
                size = cover_path.stat().st_size
                print(f"  ✅ Found: {folder.name}")
                print(f"     Cover: {cover_path} ({size:,} bytes)")
            else:
                print(f"  ❌ Folder found but NO cover.jpg: {folder.name}")
            break
    
    if not found:
        print(f"  ⚠️  Folder not found")

print(f"\n{'='*60}\n")
