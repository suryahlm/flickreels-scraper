import requests

print("Checking m3u8 format from R2...")

# Get drama list first
response = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/r2-dramas',
    headers={'Cache-Control': 'no-cache'}
)

dramas = response.json().get('dramas', [])
if not dramas:
    print("No dramas found!")
    exit(1)

# Pick first drama
sample_drama = dramas[0]
drama_title = sample_drama['title']
drama_id = sample_drama['id']
folder_name = sample_drama.get('folder_name', f"{drama_title} ({drama_id})")

print(f"\nSample drama: {drama_title}")
print(f"Folder: {folder_name}")

# Try to fetch episode 1 m3u8
m3u8_url = f"https://tender-connection-production-246f.up.railway.app/api/stream/flickreels/{folder_name}/ep01.m3u8"

print(f"\nFetching: {m3u8_url}")

try:
    m3u8_response = requests.get(m3u8_url, timeout=10)
    
    if m3u8_response.status_code != 200:
        print(f"❌ Failed to fetch m3u8: {m3u8_response.status_code}")
        print(f"Response: {m3u8_response.text[:500]}")
        exit(1)
    
    content = m3u8_response.text
    
    print("\n" + "="*60)
    print("M3U8 CONTENT (first 1000 chars):")
    print("="*60)
    print(content[:1000])
    print("="*60)
    
    # Check for adaptive streaming
    if "#EXT-X-STREAM-INF" in content:
        print("\n✅ ADAPTIVE STREAMING DETECTED!")
        print("\nThis is a MASTER PLAYLIST with multiple quality variants")
        
        # Extract variants
        lines = content.split('\n')
        variants = []
        for i, line in enumerate(lines):
            if "EXT-X-STREAM-INF" in line:
                # Get resolution
                if "RESOLUTION=" in line:
                    resolution = line.split("RESOLUTION=")[1].split(",")[0].split()[0]
                else:
                    resolution = "Unknown"
                
                # Next line is the variant URL
                if i + 1 < len(lines):
                    variant_url = lines[i + 1]
                    variants.append({
                        'resolution': resolution,
                        'url': variant_url
                    })
        
        print(f"\nFound {len(variants)} quality variants:")
        for v in variants:
            print(f"  - {v['resolution']}: {v['url']}")
        
        print("\n🎯 CONCLUSION: Tinggal setup player saja!")
        print("   Native video player sudah bisa handle multiple qualities")
        
    else:
        print("\n⚠️ SINGLE QUALITY ONLY")
        print("\nThis is a MEDIA PLAYLIST (not master)")
        print("Only one quality available")
        
        # Check if it's a valid HLS playlist
        if "#EXTM3U" in content:
            print("\n✅ Valid HLS playlist detected")
            
            # Count segments
            segments = [line for line in content.split('\n') if line.endswith('.ts')]
            print(f"   Segments: {len(segments)}")
            
            # Check target duration
            if "#EXT-X-TARGETDURATION" in content:
                target = content.split("#EXT-X-TARGETDURATION:")[1].split()[0]
                print(f"   Target duration: {target}s")
        
        print("\n🎯 CONCLUSION: Need extra work for quality selector")
        print("   Options:")
        print("   1. Check if FlickReels API has other quality URLs")
        print("   2. Transcode to multiple qualities (expensive)")
        print("   3. Keep single quality only")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
