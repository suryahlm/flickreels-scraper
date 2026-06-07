import os
import glob

print("Checking local cover files for dramas...\n")

# Dramas missing covers from screenshot
missing_dramas = [
    "Pelukan Iandar",
    "Nyonya Muda yang Tidak Terkalahin",
    "Nikah Kontrak Berujung Cinta",
    "Sekata dalam Diam",
    "Nenek Muda: Kebangkitan Keluarg",
    "Takdir Cinta dengan Kaisar",
    "Istri Kesayangan Mafia"
]

video_dir = "Video Drama TS/30.01.2026"

if not os.path.exists(video_dir):
    print(f"❌ Directory not found: {video_dir}")
    exit(1)

# Get all drama folders
folders = [f for f in os.listdir(video_dir) if os.path.isdir(os.path.join(video_dir, f))]

print(f"Total drama folders: {len(folders)}\n")
print("="*60)

found_missing = []
not_found = []

for drama_name in missing_dramas:
    # Find matching folder (partial match)
    matches = [f for f in folders if drama_name.lower() in f.lower()]
    
    if matches:
        for match in matches:
            folder_path = os.path.join(video_dir, match)
            cover_path = os.path.join(folder_path, "cover.jpg")
            
            if os.path.exists(cover_path):
                size = os.path.getsize(cover_path)
                print(f"✅ {match}")
                print(f"   Cover exists: {size:,} bytes\n")
                found_missing.append(match)
            else:
                print(f"❌ {match}")
                print(f"   Cover MISSING!\n")
                not_found.append(match)
    else:
        print(f"⚠️  {drama_name}")
        print(f"   Folder not found in local\n")
        not_found.append(drama_name)

print("="*60)
print(f"\nSummary:")
print(f"  ✅ Has cover file: {len(found_missing)}")
print(f"  ❌ Missing cover: {len(not_found)}")

if not_found:
    print(f"\n❌ Need to fix:")
    for drama in not_found:
        print(f"  - {drama}")
