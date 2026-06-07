#!/usr/bin/env python3
"""
HLS to MP4 Converter for AsianDrama R2 Bucket
==============================================
Download HLS segments from R2, merge into single MP4 using ffmpeg,
upload MP4 back to R2 (alongside existing HLS files - nothing deleted).

Usage:
    python hls_to_mp4_converter.py --count 2    # Convert first 2 dramas
    python hls_to_mp4_converter.py --start 10 --count 5  # Convert dramas 10-14
    python hls_to_mp4_converter.py --folder "Drama Name (123)"  # Convert specific drama
"""

import boto3
from botocore.config import Config
import os
import sys
import subprocess
import tempfile
import shutil
import json
import time
from pathlib import Path

# ─── Configuration ─────────────────────────────────────────────────

def load_env():
    """Load .env file from FlickReels directory."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    os.environ[k] = v.strip('"').strip("'")
        print(f"[OK] Loaded .env from {env_path}")
    else:
        print(f"[ERROR] .env not found at {env_path}")
        sys.exit(1)

def get_r2_client():
    """Create R2 (S3-compatible) client."""
    return boto3.client('s3',
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4')
    )

BUCKET = None  # Set after loading env
CDN_BASE = "https://cdn.asiandrama.cc"

# ─── R2 Operations ─────────────────────────────────────────────────

def list_flickreels_folders(r2):
    """List all drama folders in flickreels/ prefix, sorted alphabetically."""
    folders = []
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/')
    for p in resp.get('CommonPrefixes', []):
        folders.append(p['Prefix'])
    
    while resp.get('IsTruncated'):
        resp = r2.list_objects_v2(
            Bucket=BUCKET,
            Prefix='flickreels/',
            Delimiter='/',
            ContinuationToken=resp['NextContinuationToken']
        )
        for p in resp.get('CommonPrefixes', []):
            folders.append(p['Prefix'])
    
    folders.sort()
    return folders

def list_episodes_hls(r2, drama_prefix):
    """List episode folders that have HLS content (index.m3u8)."""
    episodes = []
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=drama_prefix, Delimiter='/')
    for p in resp.get('CommonPrefixes', []):
        ep_prefix = p['Prefix']
        # Only count ep_XXX/ folders
        ep_name = ep_prefix.replace(drama_prefix, '').rstrip('/')
        if ep_name.startswith('ep_'):
            episodes.append(ep_prefix)
    
    while resp.get('IsTruncated'):
        resp = r2.list_objects_v2(
            Bucket=BUCKET,
            Prefix=drama_prefix,
            Delimiter='/',
            ContinuationToken=resp['NextContinuationToken']
        )
        for p in resp.get('CommonPrefixes', []):
            ep_prefix = p['Prefix']
            ep_name = ep_prefix.replace(drama_prefix, '').rstrip('/')
            if ep_name.startswith('ep_'):
                episodes.append(ep_prefix)
    
    episodes.sort()
    return episodes

def check_mp4_exists(r2, drama_prefix, ep_name):
    """Check if MP4 already exists for this episode."""
    mp4_key = f"{drama_prefix}{ep_name}.mp4"
    try:
        r2.head_object(Bucket=BUCKET, Key=mp4_key)
        return True
    except:
        return False

def download_file(r2, key, local_path):
    """Download a file from R2 to local path."""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    r2.download_file(BUCKET, key, local_path)

def upload_mp4(r2, local_path, r2_key):
    """Upload MP4 to R2 with multipart upload for large files."""
    file_size = os.path.getsize(local_path)
    mb_size = file_size / (1024 * 1024)
    
    print(f"    📤 Uploading {mb_size:.1f}MB → {r2_key}")
    
    # Use multipart upload for files > 5MB
    config = boto3.s3.transfer.TransferConfig(
        multipart_threshold=5 * 1024 * 1024,  # 5MB
        multipart_chunksize=10 * 1024 * 1024,  # 10MB chunks
        max_concurrency=4,
    )
    
    r2.upload_file(
        local_path, BUCKET, r2_key,
        ExtraArgs={'ContentType': 'video/mp4'},
        Config=config
    )
    print(f"    ✅ Upload selesai!")

# ─── HLS Parsing & FFmpeg ──────────────────────────────────────────

def parse_m3u8(content):
    """Parse m3u8 playlist and extract segment filenames."""
    segments = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            segments.append(line)
    return segments

def merge_segments_ffmpeg(segment_files, output_path):
    """Use ffmpeg to merge TS segments into a single MP4 with faststart."""
    # Create a concat file list for ffmpeg
    concat_file = output_path + '.concat.txt'
    with open(concat_file, 'w') as f:
        for seg in segment_files:
            # Escape single quotes in filenames
            escaped = seg.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',           # No re-encoding (fast!)
        '-movflags', '+faststart',  # Enable seeking before full download
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    # Clean up concat file
    if os.path.exists(concat_file):
        os.remove(concat_file)
    
    if result.returncode != 0:
        print(f"    ❌ FFmpeg error: {result.stderr[-500:]}")
        return False
    
    return True

# ─── Main Conversion Logic ─────────────────────────────────────────

def convert_episode(r2, drama_prefix, ep_prefix, work_dir):
    """Convert a single HLS episode to MP4.
    
    Steps:
    1. Download index.m3u8 from R2
    2. Parse to find all .ts segments
    3. Download all segments
    4. Merge with ffmpeg → MP4
    5. Upload MP4 to R2 (alongside existing HLS - nothing deleted!)
    
    Returns: True if successful, False if failed
    """
    ep_name = ep_prefix.replace(drama_prefix, '').rstrip('/')
    mp4_key = f"{drama_prefix}{ep_name}.mp4"
    
    # Check if MP4 already exists
    if check_mp4_exists(r2, drama_prefix, ep_name):
        print(f"    ⏭️  {ep_name}.mp4 sudah ada, skip")
        return True
    
    ep_work_dir = os.path.join(work_dir, ep_name)
    os.makedirs(ep_work_dir, exist_ok=True)
    
    try:
        # 1. Download m3u8
        m3u8_key = f"{ep_prefix}index.m3u8"
        m3u8_local = os.path.join(ep_work_dir, 'index.m3u8')
        
        try:
            download_file(r2, m3u8_key, m3u8_local)
        except Exception as e:
            print(f"    ❌ Gagal download m3u8: {e}")
            return False
        
        with open(m3u8_local, 'r') as f:
            m3u8_content = f.read()
        
        # 2. Parse segments
        segments = parse_m3u8(m3u8_content)
        if not segments:
            print(f"    ❌ Tidak ada segment di m3u8")
            return False
        
        print(f"    📦 {len(segments)} segments ditemukan")
        
        # 3. Download all segments
        segment_files = []
        for i, seg_name in enumerate(segments):
            seg_key = f"{ep_prefix}{seg_name}"
            seg_local = os.path.join(ep_work_dir, seg_name)
            
            try:
                download_file(r2, seg_key, seg_local)
                segment_files.append(seg_local)
            except Exception as e:
                print(f"    ❌ Gagal download segment {seg_name}: {e}")
                return False
            
            # Progress indicator every 10 segments
            if (i + 1) % 10 == 0 or (i + 1) == len(segments):
                print(f"    ⬇️  Downloaded {i+1}/{len(segments)} segments", end='\r')
        
        print()  # New line after progress
        
        # 4. Merge with ffmpeg
        mp4_local = os.path.join(ep_work_dir, f'{ep_name}.mp4')
        print(f"    🔧 Merging dengan ffmpeg...")
        
        if not merge_segments_ffmpeg(segment_files, mp4_local):
            return False
        
        if not os.path.exists(mp4_local) or os.path.getsize(mp4_local) < 1000:
            print(f"    ❌ MP4 output tidak valid")
            return False
        
        # 5. Upload MP4 to R2 (HLS files tetap ada, tidak dihapus!)
        upload_mp4(r2, mp4_local, mp4_key)
        
        return True
        
    finally:
        # Cleanup temp files
        if os.path.exists(ep_work_dir):
            shutil.rmtree(ep_work_dir, ignore_errors=True)

def convert_drama(r2, drama_prefix):
    """Convert all episodes of a drama from HLS to MP4.
    
    ⚠️ SAFE: Only ADDS MP4 files. Never deletes existing HLS segments.
    """
    folder_name = drama_prefix.replace('flickreels/', '').rstrip('/')
    print(f"\n{'='*60}")
    print(f"🎬 Drama: {folder_name}")
    print(f"{'='*60}")
    
    # List episodes
    episodes = list_episodes_hls(r2, drama_prefix)
    if not episodes:
        print(f"  ⚠️  Tidak ada episode HLS ditemukan")
        return 0, 0
    
    print(f"  📋 Total episodes: {len(episodes)}")
    
    # Create temp working directory
    work_dir = os.path.join(tempfile.gettempdir(), 'hls_to_mp4', folder_name)
    os.makedirs(work_dir, exist_ok=True)
    
    success = 0
    failed = 0
    
    for ep_prefix in episodes:
        ep_name = ep_prefix.replace(drama_prefix, '').rstrip('/')
        print(f"\n  🎞️  Episode: {ep_name}")
        
        start = time.time()
        if convert_episode(r2, drama_prefix, ep_prefix, work_dir):
            elapsed = time.time() - start
            print(f"    ⏱️  {elapsed:.1f}s")
            success += 1
        else:
            failed += 1
    
    # Cleanup
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir, ignore_errors=True)
    
    print(f"\n  📊 Hasil: {success} berhasil, {failed} gagal dari {len(episodes)} episode")
    return success, failed

# ─── CLI ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert HLS to MP4 in R2')
    parser.add_argument('--count', type=int, default=2, help='Number of dramas to convert')
    parser.add_argument('--start', type=int, default=0, help='Start index (0-based)')
    parser.add_argument('--folder', type=str, help='Specific drama folder name')
    parser.add_argument('--dry-run', action='store_true', help='Only list, do not convert')
    args = parser.parse_args()
    
    # Load credentials
    load_env()
    global BUCKET
    BUCKET = os.environ['R2_BUCKET_NAME']
    
    # Create R2 client
    r2 = get_r2_client()
    
    print(f"\n🚀 HLS → MP4 Converter")
    print(f"   Bucket: {BUCKET}")
    print(f"   ⚠️  MODE AMAN: Hanya MENAMBAH file MP4, TIDAK menghapus HLS")
    print()
    
    if args.folder:
        # Convert specific drama
        prefix = f"flickreels/{args.folder}/"
        convert_drama(r2, prefix)
    else:
        # List all dramas
        print("📂 Listing drama folders...")
        folders = list_flickreels_folders(r2)
        print(f"   Total: {len(folders)} drama di R2")
        
        # Select range
        selected = folders[args.start:args.start + args.count]
        print(f"   Akan konversi: {len(selected)} drama (index {args.start}-{args.start + len(selected) - 1})")
        
        if args.dry_run:
            print("\n📋 DRY RUN - Drama yang akan dikonversi:")
            for i, f in enumerate(selected):
                name = f.replace('flickreels/', '').rstrip('/')
                eps = list_episodes_hls(r2, f)
                print(f"   {args.start + i}. {name} ({len(eps)} episodes)")
            return
        
        total_success = 0
        total_failed = 0
        
        for folder in selected:
            s, f = convert_drama(r2, folder)
            total_success += s
            total_failed += f
        
        print(f"\n{'='*60}")
        print(f"🏁 SELESAI!")
        print(f"   Total: {total_success} episode berhasil, {total_failed} gagal")
        print(f"{'='*60}")

if __name__ == '__main__':
    main()
