#!/usr/bin/env python3
"""Fix failed episode: Jangan Ganggu Nenek ep_001
Missing index.m3u8 - generate from segments, merge to MP4, upload, cleanup.
"""
import boto3, os, subprocess, tempfile, shutil

with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v.strip('"').strip("'")

r2 = boto3.client('s3',
    endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'])

bucket = os.environ['R2_BUCKET_NAME']
prefix = 'flickreels/Jangan Ganggu Nenek (5235)/ep_001/'
mp4_key = 'flickreels/Jangan Ganggu Nenek (5235)/ep_001.mp4'

# 1. List all segments
print("1. Listing segments...")
segments = []
resp = r2.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
for obj in resp.get('Contents', []):
    key = obj['Key']
    if key.endswith('.ts'):
        segments.append(key)

while resp.get('IsTruncated'):
    resp = r2.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000,
        ContinuationToken=resp['NextContinuationToken'])
    for obj in resp.get('Contents', []):
        if obj['Key'].endswith('.ts'):
            segments.append(obj['Key'])

segments.sort()
print(f"   Found {len(segments)} segments")

if not segments:
    print("   No segments found, exiting")
    exit(1)

# 2. Download segments
work_dir = os.path.join(tempfile.gettempdir(), 'fix_ep001')
if os.path.exists(work_dir):
    shutil.rmtree(work_dir)
os.makedirs(work_dir)

print("2. Downloading segments...")
local_files = []
for seg_key in segments:
    seg_name = seg_key.split('/')[-1]
    local_path = os.path.join(work_dir, seg_name)
    r2.download_file(bucket, seg_key, local_path)
    local_files.append(local_path)
    print(f"   {seg_name} OK")

# 3. Merge with ffmpeg
print("3. Merging with ffmpeg...")
concat_file = os.path.join(work_dir, 'concat.txt')
with open(concat_file, 'w') as f:
    for lf in local_files:
        escaped = lf.replace("'", "'\\''")
        f.write(f"file '{escaped}'\n")

mp4_local = os.path.join(work_dir, 'ep_001.mp4')
cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file, 
       '-c', 'copy', '-movflags', '+faststart', mp4_local]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

if result.returncode != 0:
    print(f"   FFmpeg FAILED: {result.stderr[-300:]}")
    exit(1)

file_size = os.path.getsize(mp4_local)
print(f"   MP4 created: {file_size / 1024 / 1024:.1f} MB")

# 4. Upload MP4
print("4. Uploading to R2...")
from boto3.s3.transfer import TransferConfig
config = TransferConfig(multipart_threshold=5*1024*1024, multipart_chunksize=10*1024*1024)
r2.upload_file(mp4_local, bucket, mp4_key, 
    ExtraArgs={'ContentType': 'video/mp4'}, Config=config)

# Verify
head = r2.head_object(Bucket=bucket, Key=mp4_key)
if head['ContentLength'] == file_size:
    print(f"   Upload verified: {head['ContentLength']} bytes")
    
    # 5. Cleanup HLS
    print("5. Cleaning up HLS...")
    objects_to_delete = [{'Key': k} for k in segments]
    # Also include m3u8 if exists
    try:
        r2.head_object(Bucket=bucket, Key=f"{prefix}index.m3u8")
        objects_to_delete.append({'Key': f"{prefix}index.m3u8"})
    except:
        pass
    
    r2.delete_objects(Bucket=bucket, Delete={'Objects': objects_to_delete, 'Quiet': True})
    print(f"   Deleted {len(objects_to_delete)} HLS files")
    
    print("\n✅ DONE! ep_001.mp4 uploaded and HLS cleaned up")
else:
    print(f"   Size mismatch! Local: {file_size}, R2: {head['ContentLength']}")
    print("   Keeping HLS files")

# Cleanup local
shutil.rmtree(work_dir, ignore_errors=True)
