"""
R2 Cleanup Script - Remove ID-only folders
===========================================

Removes old drama folders that only have IDs (like "2858/")
and don't follow the new format with titles (like "Drama Title (2858)/")

Usage:
    python cleanup_r2_old_folders.py --dry-run    # Preview what will be deleted
    python cleanup_r2_old_folders.py              # Actually delete
"""

import os
import re
import boto3
from botocore.config import Config

# R2 Configuration
R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", "caa84fe6b1be065cda3836f0dac4b509"),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "a4903ea93c248388b6e295d6cdbc8617"),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "asiandrama-cdn"),
    "endpoint_url": "https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com"
}

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=R2_CONFIG["endpoint_url"],
        aws_access_key_id=R2_CONFIG["access_key_id"],
        aws_secret_access_key=R2_CONFIG["secret_access_key"],
        config=Config(signature_version='s3v4')
    )

def list_flickreels_folders(client):
    """List all folders in flickreels/"""
    folders = []
    paginator = client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=R2_CONFIG["bucket_name"], Prefix="flickreels/", Delimiter="/"):
        for prefix in page.get('CommonPrefixes', []):
            folder = prefix['Prefix']
            folders.append(folder)
    
    return folders

def is_id_only_folder(folder_name):
    """Check if folder is ID-only (like 'flickreels/2858/')"""
    # Extract just the folder name after flickreels/
    match = re.match(r'^flickreels/(\d+)/$', folder_name)
    return match is not None

def get_all_objects_in_folder(client, prefix):
    """Get all objects in a folder"""
    objects = []
    paginator = client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=R2_CONFIG["bucket_name"], Prefix=prefix):
        for obj in page.get('Contents', []):
            objects.append(obj['Key'])
    
    return objects

def delete_folder(client, prefix, dry_run=True):
    """Delete all objects in a folder"""
    objects = get_all_objects_in_folder(client, prefix)
    
    if not objects:
        print(f"  No objects found in {prefix}")
        return 0
    
    if dry_run:
        print(f"  Would delete {len(objects)} objects in {prefix}")
        return len(objects)
    
    # Delete in batches of 1000
    deleted = 0
    for i in range(0, len(objects), 1000):
        batch = objects[i:i+1000]
        delete_objects = [{'Key': key} for key in batch]
        
        client.delete_objects(
            Bucket=R2_CONFIG["bucket_name"],
            Delete={'Objects': delete_objects}
        )
        deleted += len(batch)
        print(f"  Deleted {deleted}/{len(objects)} objects")
    
    return deleted

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old ID-only folders in R2")
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = parser.parse_args()
    
    print("=" * 60)
    print("R2 CLEANUP - Remove ID-only Folders")
    print("=" * 60)
    print(f"\nMode: {'DRY RUN (preview only)' if args.dry_run else 'DELETE MODE'}\n")
    
    client = get_r2_client()
    
    # Get all folders
    folders = list_flickreels_folders(client)
    print(f"Found {len(folders)} folders in flickreels/\n")
    
    # Find ID-only folders
    id_only_folders = [f for f in folders if is_id_only_folder(f)]
    titled_folders = [f for f in folders if not is_id_only_folder(f)]
    
    print(f"ID-only folders (to delete): {len(id_only_folders)}")
    print(f"Titled folders (to keep): {len(titled_folders)}")
    print()
    
    if not id_only_folders:
        print("No ID-only folders found. Nothing to clean up!")
        return
    
    print("ID-only folders to delete:")
    for folder in id_only_folders:
        print(f"  - {folder}")
    print()
    
    if not args.dry_run:
        confirm = input("Are you sure you want to delete these folders? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    
    # Delete folders
    total_deleted = 0
    for folder in id_only_folders:
        print(f"\nProcessing {folder}...")
        deleted = delete_folder(client, folder, dry_run=args.dry_run)
        total_deleted += deleted
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"DRY RUN COMPLETE: Would delete {total_deleted} objects")
    else:
        print(f"CLEANUP COMPLETE: Deleted {total_deleted} objects")
    print("=" * 60)

if __name__ == "__main__":
    main()
