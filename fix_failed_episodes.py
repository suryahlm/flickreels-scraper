#!/usr/bin/env python3
"""
Fix Failed Episodes - Manual approach: download segments, merge with ffmpeg, upload MP4.
Handles cases where the main script's convert_episode_worker fails.
"""
import sys, os, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from hls_to_mp4_concurrent import load_env, get_r2_client

load_env()
BUCKET = 'asiandrama-cdn'

EPISODES_TO_FIX = [
    ("flickreels/Cium Mawar (3877)/ep_078/", "flickreels/Cium Mawar (3877)/ep_078.mp4"),
    ("flickreels/Kutukan Nasib Sang Pengganti (2033)/ep_066/", "flickreels/Kutukan Nasib Sang Pengganti (2033)/ep_066.mp4"),
]

def fix_episode(hls_prefix, mp4_key):
    r2 = get_r2_client()
    ep_name = hls_prefix.rstrip('/').split('/')[-1]
    drama_name = hls_prefix.split('/')[1]
    
    print(f"\n🔧 {drama_name} / {ep_name}")
    
    # Check if MP4 already exists
    try:
        r2.head_object(Bucket=BUCKET, Key=mp4_key)
        print(f"   ⏭️  MP4 already exists, skipping")
        return True
    except:
        pass
    
    # Create temp directory
    tmp_dir = tempfile.mkdtemp(prefix=f"fix_{ep_name}_")
    
    try:
        # 1. Download m3u8
        print(f"   📥 Downloading m3u8...")
        m3u8_key = hls_prefix + "index.m3u8"
        m3u8_path = os.path.join(tmp_dir, "index.m3u8")
        try:
            r2.download_file(BUCKET, m3u8_key, m3u8_path)
        except Exception as e:
            print(f"   ❌ No m3u8 found: {e}")
            return False
        
        # Parse m3u8
        with open(m3u8_path, 'r') as f:
            content = f.read()
        segments = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        print(f"   📋 Found {len(segments)} segments")
        
        # 2. Download all segments
        print(f"   📥 Downloading segments...")
        seg_files = []
        for seg_name in segments:
            seg_key = hls_prefix + seg_name
            seg_path = os.path.join(tmp_dir, seg_name)
            try:
                r2.download_file(BUCKET, seg_key, seg_path)
                seg_files.append(seg_path)
            except Exception as e:
                print(f"   ⚠️  Missing segment {seg_name}: {e}")
                return False
        
        print(f"   ✅ Downloaded {len(seg_files)} segments")
        
        # 3. Merge with ffmpeg
        print(f"   🔨 Merging with ffmpeg...")
        concat_file = os.path.join(tmp_dir, "concat.txt")
        with open(concat_file, 'w') as f:
            for seg in seg_files:
                f.write(f"file '{seg}'\n")
        
        mp4_path = os.path.join(tmp_dir, f"{ep_name}.mp4")
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            mp4_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            print(f"   ❌ ffmpeg failed: {result.stderr.decode()[-200:]}")
            return False
        
        mp4_size = os.path.getsize(mp4_path) / 1024 / 1024
        print(f"   ✅ MP4 created: {mp4_size:.1f} MB")
        
        # 4. Upload to R2
        print(f"   📤 Uploading to R2...")
        r2.upload_file(mp4_path, BUCKET, mp4_key, ExtraArgs={'ContentType': 'video/mp4'})
        
        # Verify
        r2.head_object(Bucket=BUCKET, Key=mp4_key)
        print(f"   ✅ Upload verified!")
        
        # 5. Cleanup HLS
        print(f"   🗑️  Cleaning HLS...")
        resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=hls_prefix)
        for obj in resp.get('Contents', []):
            r2.delete_object(Bucket=BUCKET, Key=obj['Key'])
        deleted = len(resp.get('Contents', []))
        print(f"   ✅ Deleted {deleted} HLS files")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    print(f"\n🔧 Fixing {len(EPISODES_TO_FIX)} failed episodes...\n")
    
    success = 0
    for hls_prefix, mp4_key in EPISODES_TO_FIX:
        if fix_episode(hls_prefix, mp4_key):
            success += 1
    
    print(f"\n🏁 Done! {success}/{len(EPISODES_TO_FIX)} fixed")
    
    print(f"\n⚠️  Note: 'Saat kita bertemu lagi (2169) ep_059' is NOT fixable")
    print(f"   (missing index.m3u8 + segment_0006.ts — source data incomplete)")


if __name__ == '__main__':
    main()
