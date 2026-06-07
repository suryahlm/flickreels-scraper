#!/usr/bin/env python3
"""Check R2 status of failed episodes"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from hls_to_mp4_concurrent import load_env, get_r2_client

load_env()
r2 = get_r2_client()
BUCKET = 'asiandrama-cdn'

episodes = [
    ("flickreels/Cium Mawar (3877)/ep_078/", "Cium Mawar ep_078"),
    ("flickreels/Kutukan Nasib Sang Pengganti (2033)/ep_066/", "Kutukan ep_066"),
    ("flickreels/Saat kita bertemu lagi (2169)/ep_059/", "Saat kita ep_059"),
]

for prefix, label in episodes:
    print(f"\n📂 {label}:")
    resp = r2.list_objects_v2(Bucket=BUCKET, Prefix=prefix, MaxKeys=20)
    contents = resp.get('Contents', [])
    if not contents:
        print("   ❌ EMPTY - No files found")
    else:
        for obj in contents:
            key = obj['Key'].split('/')[-1]
            size_mb = obj['Size'] / 1024 / 1024
            print(f"   📄 {key} ({size_mb:.1f} MB)")
