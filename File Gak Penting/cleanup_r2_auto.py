#!/usr/bin/env python3
"""
R2 Cleanup Script - Delete non-Indonesian drama folders (auto mode)
Keeps only the 42 Indonesian dramas with covers
"""
import boto3
from botocore.config import Config
import re

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# 42 Indonesian dramas WITH COVERS to KEEP
KEEP_IDS = {
    '894', '5190', '5136', '3108', '5119', '721', '978', '5194', '5122', '487', '5071', '4009',
    '3495', '5137', '495', '977', '5235', '5202', '963', '5089', '5159', '3985', '4464', '4784',
    '533', '5135', '2186', '3674', '4187', '4158', '2518', '5220', '5031', '5247', '5099', '4511',
    '4839', '5043', '3164', '5226', '2858', '1445',
}

def get_all_folders():
    """Get all drama folders in R2"""
    folders = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append(prefix['Prefix'])
    return folders

def extract_id(folder_name):
    """Extract drama ID from folder name like 'Title (1234)'"""
    match = re.search(r'\((\d+)\)$', folder_name)
    return match.group(1) if match else None

def delete_folder(prefix):
    """Delete all objects in a folder"""
    deleted_count = 0
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects = page.get('Contents', [])
        if objects:
            delete_keys = [{'Key': obj['Key']} for obj in objects]
            s3.delete_objects(Bucket=bucket, Delete={'Objects': delete_keys})
            deleted_count += len(delete_keys)
    return deleted_count

def main():
    print("=" * 60)
    print("R2 CLEANUP - AUTO MODE")
    print("=" * 60)
    
    folders = get_all_folders()
    print(f"\nTotal folders in R2: {len(folders)}")
    print(f"Indonesian dramas to KEEP: {len(KEEP_IDS)}")
    
    # Categorize
    to_keep = []
    to_delete = []
    
    for folder in folders:
        folder_name = folder.replace('flickreels/', '').replace('/', '')
        if not folder_name or folder_name in ['dramas', 'test']:
            continue
        
        drama_id = extract_id(folder_name)
        if drama_id and drama_id in KEEP_IDS:
            to_keep.append((folder, folder_name))
        else:
            to_delete.append((folder, folder_name))
    
    print(f"\nFolders to KEEP: {len(to_keep)}")
    print(f"Folders to DELETE: {len(to_delete)}")
    
    if not to_delete:
        print("\nNo folders to delete!")
        return
    
    # Delete without confirmation (auto mode)
    print(f"\n⚠️  Deleting {len(to_delete)} folders...")
    total_deleted = 0
    
    for i, (folder, name) in enumerate(to_delete):
        count = delete_folder(folder)
        total_deleted += count
        print(f"  [{i+1}/{len(to_delete)}] Deleted {name} ({count} objects)")
    
    print(f"\n✅ CLEANUP COMPLETE!")
    print(f"   Deleted {len(to_delete)} folders")
    print(f"   Deleted {total_deleted} total objects")

if __name__ == "__main__":
    main()
