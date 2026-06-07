#!/usr/bin/env python3
"""
HLS to MP4 Concurrent Converter for AsianDrama R2 Bucket
=========================================================
Converts HLS segments to MP4 using 10 parallel workers.
Auto-cleans HLS files after successful MP4 upload.
Auto-updates Supabase video_format after each drama completes.

Usage:
    python hls_to_mp4_concurrent.py --count 100    # Convert 100 dramas (skip first 2 already done)
    python hls_to_mp4_concurrent.py --count 50 --start 10  # Convert dramas 10-59
    python hls_to_mp4_concurrent.py --workers 8    # Use 8 parallel workers
    python hls_to_mp4_concurrent.py --dry-run --count 100  # Preview only
    python hls_to_mp4_concurrent.py --keep-hls          # Keep HLS files (no cleanup)

Flow per episode:
    1. Download HLS segments from R2
    2. Merge → MP4 locally with ffmpeg
    3. Upload MP4 to R2
    4. Verify MP4 exists on R2
    5. Delete old HLS folder (m3u8 + .ts segments) from R2
    ⚡ Auto-skips episodes where MP4 already exists.
    📝 Logs to hls_conversion.log for overnight monitoring.
"""

import boto3
from botocore.config import Config
import os
import sys
import subprocess
import tempfile
import shutil
import time
import logging
import threading
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# ─── Configuration ─────────────────────────────────────────────────

WORKERS = 10  # Default parallel workers
SUPABASE_URL = "https://bmryonqbddbkjbtquhgu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ"
BUCKET = None

# Thread-local storage for R2 clients
_thread_local = threading.local()

# Global progress counter
_progress_lock = threading.Lock()
_total_success = 0
_total_failed = 0
_total_skipped = 0
_total_cleaned = 0  # HLS folders deleted
_keep_hls = False   # Set via --keep-hls flag

# ─── Logging ───────────────────────────────────────────────────────

def setup_logging():
    """Setup dual logging: file + console."""
    log_path = os.path.join(os.path.dirname(__file__), 'hls_conversion.log')
    
    # File handler - detailed
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'
    ))
    
    # Console handler - concise
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    
    logger = logging.getLogger('converter')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

log = setup_logging()

# ─── Environment & R2 ─────────────────────────────────────────────

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
        log.info(f"[OK] Loaded .env from {env_path}")
    else:
        log.error(f".env not found at {env_path}")
        sys.exit(1)

def get_r2_client():
    """Get thread-local R2 client (each thread gets its own connection)."""
    if not hasattr(_thread_local, 'r2'):
        _thread_local.r2 = boto3.client('s3',
            endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
            config=Config(signature_version='s3v4')
        )
    return _thread_local.r2

# ─── R2 Operations ─────────────────────────────────────────────────

def list_flickreels_folders(r2):
    """List all drama folders in flickreels/ prefix, sorted alphabetically."""
    folders = []
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix='flickreels/', Delimiter='/')
    for p in resp.get('CommonPrefixes', []):
        folders.append(p['Prefix'])
    
    while resp.get('IsTruncated'):
        resp = r2.list_objects_v2(
            Bucket=BUCKET, Prefix='flickreels/', Delimiter='/',
            ContinuationToken=resp['NextContinuationToken']
        )
        for p in resp.get('CommonPrefixes', []):
            folders.append(p['Prefix'])
    
    folders.sort()
    return folders

def list_episodes_hls(r2, drama_prefix):
    """List episode folders that have HLS content."""
    episodes = []
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=drama_prefix, Delimiter='/')
    for p in resp.get('CommonPrefixes', []):
        ep_name = p['Prefix'].replace(drama_prefix, '').rstrip('/')
        if ep_name.startswith('ep_'):
            episodes.append(p['Prefix'])
    
    while resp.get('IsTruncated'):
        resp = r2.list_objects_v2(
            Bucket=BUCKET, Prefix=drama_prefix, Delimiter='/',
            ContinuationToken=resp['NextContinuationToken']
        )
        for p in resp.get('CommonPrefixes', []):
            ep_name = p['Prefix'].replace(drama_prefix, '').rstrip('/')
            if ep_name.startswith('ep_'):
                episodes.append(p['Prefix'])
    
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

def delete_hls_folder(r2, ep_prefix):
    """Delete all HLS files in an episode folder from R2.
    
    Deletes: index.m3u8 + all .ts segment files.
    Only called AFTER MP4 upload is verified.
    
    Returns: number of objects deleted
    """
    deleted = 0
    try:
        # List all objects in the episode folder
        objects_to_delete = []
        resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=ep_prefix)
        
        for obj in resp.get('Contents', []):
            objects_to_delete.append({'Key': obj['Key']})
        
        while resp.get('IsTruncated'):
            resp = r2.list_objects_v2(
                Bucket=BUCKET, Prefix=ep_prefix,
                ContinuationToken=resp['NextContinuationToken']
            )
            for obj in resp.get('Contents', []):
                objects_to_delete.append({'Key': obj['Key']})
        
        if objects_to_delete:
            # R2 supports batch delete up to 1000 objects
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                r2.delete_objects(
                    Bucket=BUCKET,
                    Delete={'Objects': batch, 'Quiet': True}
                )
                deleted += len(batch)
    except Exception as e:
        log.debug(f"Error deleting HLS folder {ep_prefix}: {e}")
    
    return deleted

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
    concat_file = output_path + '.concat.txt'
    with open(concat_file, 'w') as f:
        for seg in segment_files:
            escaped = seg.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
    
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_file, '-c', 'copy',
        '-movflags', '+faststart', output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if os.path.exists(concat_file):
        os.remove(concat_file)
    
    if result.returncode != 0:
        log.error(f"FFmpeg error: {result.stderr[-300:]}")
        return False
    return True

# ─── Episode Conversion (thread-safe) ─────────────────────────────

def convert_episode_worker(drama_prefix, ep_prefix):
    """Convert a single HLS episode to MP4. Thread-safe.
    
    Returns: (ep_name, 'success'|'skipped'|'failed', time_seconds)
    """
    global _total_success, _total_failed, _total_skipped
    
    r2 = get_r2_client()
    ep_name = ep_prefix.replace(drama_prefix, '').rstrip('/')
    mp4_key = f"{drama_prefix}{ep_name}.mp4"
    start_time = time.time()
    
    # Check if MP4 already exists
    if check_mp4_exists(r2, drama_prefix, ep_name):
        with _progress_lock:
            _total_skipped += 1
        return (ep_name, 'skipped', 0)
    
    # Create isolated work directory for this thread
    work_dir = os.path.join(
        tempfile.gettempdir(), 'hls_to_mp4',
        f"worker_{threading.current_thread().name}",
        ep_name
    )
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # 1. Download m3u8
        m3u8_key = f"{ep_prefix}index.m3u8"
        m3u8_local = os.path.join(work_dir, 'index.m3u8')
        
        try:
            r2.download_file(BUCKET, m3u8_key, m3u8_local)
        except Exception as e:
            log.debug(f"Failed to download m3u8 for {ep_name}: {e}")
            with _progress_lock:
                _total_failed += 1
            return (ep_name, 'failed', time.time() - start_time)
        
        with open(m3u8_local, 'r') as f:
            m3u8_content = f.read()
        
        # 2. Parse segments
        segments = parse_m3u8(m3u8_content)
        if not segments:
            with _progress_lock:
                _total_failed += 1
            return (ep_name, 'failed', time.time() - start_time)
        
        # 3. Download all segments
        segment_files = []
        for seg_name in segments:
            seg_key = f"{ep_prefix}{seg_name}"
            seg_local = os.path.join(work_dir, seg_name)
            os.makedirs(os.path.dirname(seg_local), exist_ok=True)
            
            try:
                r2.download_file(BUCKET, seg_key, seg_local)
                segment_files.append(seg_local)
            except Exception as e:
                log.debug(f"Failed to download segment {seg_name}: {e}")
                with _progress_lock:
                    _total_failed += 1
                return (ep_name, 'failed', time.time() - start_time)
        
        # 4. Merge with ffmpeg
        mp4_local = os.path.join(work_dir, f'{ep_name}.mp4')
        if not merge_segments_ffmpeg(segment_files, mp4_local):
            with _progress_lock:
                _total_failed += 1
            return (ep_name, 'failed', time.time() - start_time)
        
        if not os.path.exists(mp4_local) or os.path.getsize(mp4_local) < 1000:
            with _progress_lock:
                _total_failed += 1
            return (ep_name, 'failed', time.time() - start_time)
        
        # 5. Upload MP4 to R2
        file_size = os.path.getsize(mp4_local)
        upload_config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=5 * 1024 * 1024,
            multipart_chunksize=10 * 1024 * 1024,
            max_concurrency=4,
        )
        r2.upload_file(
            mp4_local, BUCKET, mp4_key,
            ExtraArgs={'ContentType': 'video/mp4'},
            Config=upload_config
        )
        
        # 6. Verify MP4 on R2, then cleanup HLS
        if not _keep_hls:
            # Double-check MP4 exists before deleting HLS
            try:
                head = r2.head_object(Bucket=BUCKET, Key=mp4_key)
                r2_size = head['ContentLength']
                local_size = os.path.getsize(mp4_local)
                
                if r2_size == local_size:
                    # Sizes match — safe to delete HLS folder
                    cleaned = delete_hls_folder(r2, ep_prefix)
                    with _progress_lock:
                        global _total_cleaned
                        _total_cleaned += cleaned
                else:
                    log.warning(f"Size mismatch for {ep_name}: local={local_size}, r2={r2_size}. Keeping HLS.")
            except Exception as e:
                log.warning(f"Cannot verify MP4 for {ep_name}, keeping HLS: {e}")
        
        elapsed = time.time() - start_time
        with _progress_lock:
            _total_success += 1
        
        return (ep_name, 'success', elapsed)
        
    except Exception as e:
        log.debug(f"Unexpected error converting {ep_name}: {e}")
        with _progress_lock:
            _total_failed += 1
        return (ep_name, 'failed', time.time() - start_time)
    finally:
        # Cleanup temp files
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)

# ─── Supabase Update ──────────────────────────────────────────────

def update_supabase_video_format(folder_name):
    """Update Supabase source_data.video_format to 'mp4' for a drama.
    
    Extracts FlickReels ID from folder name like "Drama Name (1234)".
    """
    # Extract ID from folder name: "Drama Name (1234)" → "1234"
    import re
    match = re.search(r'\((\d+)\)$', folder_name)
    if not match:
        log.warning(f"Cannot extract ID from folder: {folder_name}")
        return False
    
    fid = match.group(1)
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        # Get current source_data
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{fid}&select=source_data",
            headers=headers, timeout=10
        )
        
        if resp.status_code == 200 and resp.json():
            source_data = resp.json()[0].get("source_data") or {}
            source_data["video_format"] = "mp4"
            
            update_resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{fid}",
                headers=headers,
                json={"source_data": source_data},
                timeout=10
            )
            
            if update_resp.status_code in [200, 204]:
                log.info(f"  📡 Supabase updated: fid={fid} → video_format='mp4'")
                return True
            else:
                log.warning(f"  ⚠️  Supabase update failed: {update_resp.status_code}")
        else:
            log.debug(f"Drama fid={fid} not found in Supabase")
    except Exception as e:
        log.warning(f"  ⚠️  Supabase error: {e}")
    
    return False

# ─── Drama Conversion (concurrent episodes) ───────────────────────

def convert_drama_concurrent(drama_prefix, workers, drama_num, total_dramas):
    """Convert all episodes of a drama using parallel workers."""
    global _total_success, _total_failed, _total_skipped
    
    r2 = get_r2_client()
    folder_name = drama_prefix.replace('flickreels/', '').rstrip('/')
    
    log.info(f"\n{'='*60}")
    log.info(f"🎬 [{drama_num}/{total_dramas}] {folder_name}")
    log.info(f"{'='*60}")
    
    # List episodes
    episodes = list_episodes_hls(r2, drama_prefix)
    if not episodes:
        log.info(f"  ⚠️  No HLS episodes found")
        return 0, 0, 0
    
    log.info(f"  📋 {len(episodes)} episodes | {workers} workers")
    
    drama_success = 0
    drama_failed = 0
    drama_skipped = 0
    drama_start = time.time()
    
    # Convert episodes in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(convert_episode_worker, drama_prefix, ep): ep
            for ep in episodes
        }
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            ep_name, status, elapsed = future.result()
            
            if status == 'success':
                drama_success += 1
                size_info = f"{elapsed:.1f}s"
            elif status == 'skipped':
                drama_skipped += 1
                size_info = "skip"
            else:
                drama_failed += 1
                size_info = "FAIL"
            
            # Progress line
            log.info(f"  [{completed}/{len(episodes)}] {ep_name} → {size_info}")
    
    drama_elapsed = time.time() - drama_start
    log.info(f"  📊 ✅{drama_success} ❌{drama_failed} ⏭️{drama_skipped} | {drama_elapsed:.0f}s")
    
    # Auto-update Supabase if any episodes were successfully converted
    if drama_success > 0:
        update_supabase_video_format(folder_name)
    
    return drama_success, drama_failed, drama_skipped

# ─── CLI ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Concurrent HLS→MP4 Converter')
    parser.add_argument('--count', type=int, default=100, help='Number of dramas (default: 100)')
    parser.add_argument('--start', type=int, default=2, help='Start index, skip first N (default: 2, skip already converted)')
    parser.add_argument('--workers', type=int, default=WORKERS, help=f'Parallel workers (default: {WORKERS})')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no conversion')
    parser.add_argument('--keep-hls', action='store_true', help='Keep HLS files (do not cleanup after conversion)')
    args = parser.parse_args()
    
    global _keep_hls
    _keep_hls = args.keep_hls
    
    # Load credentials
    load_env()
    global BUCKET
    BUCKET = os.environ['R2_BUCKET_NAME']
    
    # Create initial R2 client
    r2 = get_r2_client()
    
    start_time = datetime.now()
    log.info(f"")
    log.info(f"🚀 HLS → MP4 Concurrent Converter")
    log.info(f"   Bucket: {BUCKET}")
    log.info(f"   Workers: {args.workers} parallel")
    log.info(f"   Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if _keep_hls:
        log.info(f"   ⚠️  KEEP HLS: File HLS TIDAK akan dihapus")
    else:
        log.info(f"   🗑️  AUTO-CLEANUP: HLS dihapus setelah MP4 verified")
    log.info(f"   📝 Log: hls_conversion.log")
    log.info(f"")
    
    # List all dramas
    log.info("📂 Listing drama folders...")
    folders = list_flickreels_folders(r2)
    log.info(f"   Total di R2: {len(folders)} drama")
    
    # Select range
    selected = folders[args.start:args.start + args.count]
    log.info(f"   Akan konversi: {len(selected)} drama (index {args.start}-{args.start + len(selected) - 1})")
    log.info(f"")
    
    if args.dry_run:
        log.info("📋 DRY RUN - Drama yang akan dikonversi:")
        for i, f in enumerate(selected):
            name = f.replace('flickreels/', '').rstrip('/')
            eps = list_episodes_hls(r2, f)
            log.info(f"   {args.start + i}. {name} ({len(eps)} episodes)")
        
        total_eps = sum(len(list_episodes_hls(r2, f)) for f in selected)
        est_minutes = total_eps * 30 / args.workers / 60  # ~30s per ep, divided by workers
        log.info(f"\n   📊 Total: {total_eps} episodes")
        log.info(f"   ⏱️  Estimasi: ~{est_minutes:.0f} menit ({est_minutes/60:.1f} jam) dengan {args.workers} workers")
        return
    
    # Convert!
    global _total_success, _total_failed, _total_skipped
    _total_success = 0
    _total_failed = 0
    _total_skipped = 0
    
    for i, folder in enumerate(selected):
        convert_drama_concurrent(folder, args.workers, i + 1, len(selected))
    
    end_time = datetime.now()
    elapsed = end_time - start_time
    hours = elapsed.total_seconds() / 3600
    
    log.info(f"\n{'='*60}")
    log.info(f"🏁 SELESAI!")
    log.info(f"   ✅ Berhasil: {_total_success} episode")
    log.info(f"   ❌ Gagal: {_total_failed} episode")
    log.info(f"   ⏭️  Skipped: {_total_skipped} episode (MP4 sudah ada)")
    log.info(f"   🗑️  Cleaned: {_total_cleaned} HLS files dihapus")
    log.info(f"   ⏱️  Total waktu: {hours:.1f} jam")
    log.info(f"   Started: {start_time.strftime('%H:%M:%S')}")
    log.info(f"   Finished: {end_time.strftime('%H:%M:%S')}")
    log.info(f"{'='*60}")

if __name__ == '__main__':
    main()
