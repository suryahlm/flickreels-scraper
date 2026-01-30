"""
Cloudflare R2 Video Uploader

Uploads downloaded HLS videos to Cloudflare R2 bucket.
Maintains same folder structure for direct streaming.

Prerequisites:
    pip install boto3

Environment Variables Required:
    R2_ACCOUNT_ID     - Cloudflare Account ID
    R2_ACCESS_KEY_ID  - R2 API Token Access Key
    R2_SECRET_ACCESS_KEY - R2 API Token Secret Key
    R2_BUCKET_NAME    - R2 Bucket name (e.g., "flickreels")

Usage:
    python upload_to_r2.py                           # Upload all from default dir
    python upload_to_r2.py --input ./Scraping/2026-01-30  # Specific folder
    python upload_to_r2.py --drama-ids 2858,533      # Upload specific dramas
    python upload_to_r2.py --dry-run                 # Preview without uploading
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

# Load .env file if exists
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT_DIR = BASE_DIR / "Video Drama TS" / datetime.now().strftime("%d.%m.%Y")

# R2 Configuration from environment
R2_CONFIG = {
    "account_id": os.environ.get("R2_ACCOUNT_ID", ""),
    "access_key_id": os.environ.get("R2_ACCESS_KEY_ID", ""),
    "secret_access_key": os.environ.get("R2_SECRET_ACCESS_KEY", ""),
    "bucket_name": os.environ.get("R2_BUCKET_NAME", "asiandrama-cdn"),
}

# Content types for file extensions
CONTENT_TYPES = {
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".json": "application/json",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

# ============================================================================
# R2 UPLOADER CLASS
# ============================================================================

class R2Uploader:
    def __init__(self, input_dir: Path, bucket_name: str, prefix: str = "dramas"):
        self.input_dir = input_dir
        self.bucket_name = bucket_name
        self.prefix = prefix  # R2 folder structure: dramas/DramaTitle/ep_xxx.m3u8
        self.dry_run = False
        
        # Statistics
        self.stats = {
            "files_uploaded": 0,
            "files_skipped": 0,
            "bytes_uploaded": 0,
            "errors": 0
        }
        
        # Initialize S3 client for R2
        self.s3 = None
    
    def connect(self) -> bool:
        """Connect to Cloudflare R2 using boto3."""
        if not R2_CONFIG["account_id"] or not R2_CONFIG["access_key_id"]:
            print("\n[ERROR] R2 credentials not configured!")
            print("Please set environment variables:")
            print("  - R2_ACCOUNT_ID")
            print("  - R2_ACCESS_KEY_ID")
            print("  - R2_SECRET_ACCESS_KEY")
            print("  - R2_BUCKET_NAME (optional, default: asiandrama-cdn)")
            return False
        
        try:
            endpoint_url = f"https://{R2_CONFIG['account_id']}.r2.cloudflarestorage.com"
            
            self.s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=R2_CONFIG["access_key_id"],
                aws_secret_access_key=R2_CONFIG["secret_access_key"],
                config=Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"}
                )
            )
            
            # Test connection with HeadBucket (doesn't require ListBuckets permission)
            try:
                self.s3.head_bucket(Bucket=self.bucket_name)
                print(f"[OK] Connected to R2 bucket: {self.bucket_name}")
            except Exception as e:
                print(f"[WARN] Could not verify bucket, will try to upload anyway: {e}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to connect to R2: {e}")
            return False
    
    def get_content_type(self, file_path: Path) -> str:
        """Get content type based on file extension."""
        return CONTENT_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
    
    def upload_file(self, local_path: Path, r2_key: str) -> bool:
        """Upload a single file to R2."""
        if self.dry_run:
            print(f"  [DRY-RUN] Would upload: {r2_key}")
            return True
        
        try:
            content_type = self.get_content_type(local_path)
            file_size = local_path.stat().st_size
            
            with open(local_path, 'rb') as f:
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=r2_key,
                    Body=f,
                    ContentType=content_type,
                    CacheControl="public, max-age=31536000"  # 1 year cache
                )
            
            self.stats["files_uploaded"] += 1
            self.stats["bytes_uploaded"] += file_size
            return True
            
        except Exception as e:
            print(f"  [ERROR] Failed to upload {r2_key}: {e}")
            self.stats["errors"] += 1
            return False
    
    def check_file_exists(self, r2_key: str) -> bool:
        """Check if file already exists in R2."""
        if self.dry_run:
            return False
        
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=r2_key)
            return True
        except:
            return False
    
    def upload_drama(self, drama_folder: str, skip_existing: bool = True) -> bool:
        """Upload all files for a single drama folder."""
        drama_dir = self.input_dir / drama_folder
        
        if not drama_dir.exists():
            print(f"  [WARN] Drama directory not found: {drama_dir}")
            return False
        
        print(f"\n[DRAMA] Uploading: {drama_folder}")
        
        # Get all files in drama directory
        files = list(drama_dir.glob("*"))
        total_files = len(files)
        
        for i, file_path in enumerate(files):
            if not file_path.is_file():
                continue
            
            # Build R2 key: dramas/DramaFolderName/filename
            r2_key = f"{self.prefix}/{drama_folder}/{file_path.name}"
            
            # Skip if exists
            if skip_existing and self.check_file_exists(r2_key):
                self.stats["files_skipped"] += 1
                continue
            
            # Upload
            self.upload_file(file_path, r2_key)
            
            # Progress
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{total_files} files")
        
        print(f"  Done: {total_files} files")
        return True
    
    def upload_all(self, drama_folders: Optional[List[str]] = None, 
                   skip_existing: bool = True):
        """Upload all dramas to R2."""
        
        # Check input directory
        if not self.input_dir.exists():
            print(f"[ERROR] Input directory not found: {self.input_dir}")
            return
        
        # Get list of drama folders (all directories in input_dir)
        all_dramas = [d.name for d in self.input_dir.iterdir() if d.is_dir()]
        
        if drama_folders:
            dramas_to_upload = [d for d in all_dramas if d in drama_folders]
        else:
            dramas_to_upload = all_dramas
        
        print(f"\n{'='*60}")
        print(f"R2 Upload - {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"{'='*60}")
        print(f"  Input:        {self.input_dir}")
        print(f"  Bucket:       {self.bucket_name}")
        print(f"  Prefix:       {self.prefix}")
        print(f"  Dramas:       {len(dramas_to_upload)}")
        print(f"  Skip existing: {skip_existing}")
        print(f"{'='*60}")
        
        if not self.dry_run and not self.connect():
            return
        
        # Upload each drama folder
        for drama_folder in dramas_to_upload:
            self.upload_drama(drama_folder, skip_existing)
        
        # Print statistics
        print(f"\n{'='*60}")
        print(f"UPLOAD COMPLETE")
        print(f"{'='*60}")
        print(f"  Files uploaded: {self.stats['files_uploaded']}")
        print(f"  Files skipped:  {self.stats['files_skipped']}")
        print(f"  Total data:     {self.stats['bytes_uploaded'] / (1024*1024):.1f} MB")
        print(f"  Errors:         {self.stats['errors']}")
        print(f"{'='*60}")
        
        # Print R2 public URL
        if not self.dry_run and self.stats["files_uploaded"] > 0:
            print(f"\n[INFO] Your R2 Public URL:")
            print(f"  https://pub-{R2_CONFIG['account_id'][:16]}.r2.dev/{self.prefix}/")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Upload videos to Cloudflare R2")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT_DIR),
                        help="Input directory with downloaded videos")
    parser.add_argument("--bucket", type=str, default=R2_CONFIG["bucket_name"],
                        help="R2 bucket name")
    parser.add_argument("--prefix", type=str, default="flickreels",
                        help="R2 key prefix (folder)")
    parser.add_argument("--drama-ids", type=str, default=None,
                        help="Comma-separated drama IDs to upload")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip files that already exist in R2")
    parser.add_argument("--dry-run", action="store_true", default=False,
                        help="Preview upload without actually uploading")
    
    args = parser.parse_args()
    
    # Parse drama folders
    drama_folders = None
    if args.drama_ids:
        drama_folders = [x.strip() for x in args.drama_ids.split(',')]
    
    # Create uploader
    uploader = R2Uploader(
        input_dir=Path(args.input),
        bucket_name=args.bucket,
        prefix=args.prefix
    )
    uploader.dry_run = args.dry_run
    
    # Run upload
    uploader.upload_all(
        drama_folders=drama_folders,
        skip_existing=args.skip_existing
    )


if __name__ == "__main__":
    main()
