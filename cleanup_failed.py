#!/usr/bin/env python3
"""Cleanup orphaned HLS files for episodes that already have MP4"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from hls_to_mp4_concurrent import load_env, get_r2_client

load_env()
BUCKET = 'asiandrama-cdn'

# HLS folders to clean (MP4 already exists)
CLEANUP = [
    "flickreels/Cium Mawar (3877)/ep_078/",
    "flickreels/Kutukan Nasib Sang Pengganti (2033)/ep_066/",
    "flickreels/Saat kita bertemu lagi (2169)/ep_059/",  # incomplete source, cleanup anyway
]

def main():
    r2 = get_r2_client()
    total_deleted = 0
    
    for prefix in CLEANUP:
        name = '/'.join(prefix.rstrip('/').split('/')[-2:])
        resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        contents = resp.get('Contents', [])
        if not contents:
            print(f"  ⏭️  {name} — already clean")
            continue
        
        for obj in contents:
            r2.delete_object(Bucket=BUCKET, Key=obj['Key'])
        total_deleted += len(contents)
        print(f"  🗑️  {name} — deleted {len(contents)} files")
    
    print(f"\n✅ Total cleaned: {total_deleted} orphaned HLS files")

if __name__ == '__main__':
    main()
