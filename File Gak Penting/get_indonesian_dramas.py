#!/usr/bin/env python3
"""Identify Indonesian dramas from R2 by title analysis."""
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

# List all folders
folders = []
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix='flickreels/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        folders.append(prefix['Prefix'])

print(f"Total folders: {len(folders)}\n")

# Keywords that indicate NON-Indonesian (other languages)
non_indo_patterns = [
    # French
    r'\bau\b', r'\bdu\b', r'\ble\b', r'\bla\b', r'\bles\b', r'\bun\b', r'\bune\b', r'\bdes\b',
    r'\bsauvez\b', r'\bChasse\b', r'\bAmour\b', r'\bDurée\b', r'\bLimitée\b', r'\bjeune\b',
    # Portuguese/Spanish
    r'\bé\b', r'\bmãe\b', r'\bpresidente\b', r'\bmédica\b', r'\bdivino\b', r'\bfamília\b',
    r'\bCamino\b', r'\bgloria\b', r'\btecho\b', r'\bCordero\b', r'\bMundos\b',
    r'\bfaxineira\b', r'\bCasamento\b', r'\bimperatriz\b', r'\bModerno\b',
    # English
    r'\bHeiress\'s\b', r'\bRise\b', r'\bFrom\b', r'\bExile\b', r'\bEmpire\b', r'\bBeyond\b',
    r'\bStatus\b', r'\bHeart\'s\b', r'\bTrue\b', r'\bJourney\b', r'\bKiss\b', r'\bThorny\b',
    r'\bRose\b', r'\bBlooms\b', r'\bDivorce\b', r'\bDubbed\b', r'\bUltimate\b', r'\bFavor\b',
    r'\bNew\b', r'\bLife\b', r'\bAfter\b',
    # Special markers
    r'Dubbed\)', r'\(Dubbed\)',
]

# Compile patterns
non_indo_regex = re.compile('|'.join(non_indo_patterns), re.IGNORECASE)

indonesian = []
non_indonesian = []

for folder in folders:
    folder_name = folder.replace('flickreels/', '').replace('/', '')
    if not folder_name or folder_name in ['dramas', 'test']:
        continue
    
    # Extract ID
    match = re.search(r'\((\d+)\)$', folder_name)
    drama_id = match.group(1) if match else None
    
    # Check if has video content
    has_video = False
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}ep_', MaxKeys=3)
        if resp.get('Contents'):
            has_video = True
    except:
        pass
    if not has_video:
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=f'{folder}episodes/', MaxKeys=3)
            if resp.get('Contents'):
                has_video = True
        except:
            pass
    
    if not has_video or not drama_id:
        continue
    
    # Check title
    title = folder_name.rsplit(' (', 1)[0] if ' (' in folder_name else folder_name
    
    if non_indo_regex.search(title):
        non_indonesian.append((drama_id, title))
    else:
        indonesian.append((drama_id, title))

print(f"INDONESIAN DRAMAS: {len(indonesian)}")
print(f"NON-INDONESIAN: {len(non_indonesian)}")

print("\n--- INDONESIAN DRAMAS ---")
for id, title in sorted(indonesian, key=lambda x: x[1]):
    print(f"  '{id}': {title}")

print("\n--- NON-INDONESIAN (to exclude) ---")
for id, title in sorted(non_indonesian, key=lambda x: x[1])[:30]:
    print(f"  '{id}': {title}")
if len(non_indonesian) > 30:
    print(f"  ... and {len(non_indonesian)-30} more")

# Output TypeScript set for Indonesian IDs
print("\n\n// TypeScript Set for INDONESIAN drama IDs:")
print("const INDONESIAN_DRAMA_IDS = new Set([")
indo_ids = [id for id, _ in indonesian]
chunks = [indo_ids[i:i+12] for i in range(0, len(indo_ids), 12)]
for chunk in chunks:
    formatted = ', '.join([f"'{id}'" for id in chunk])
    print(f"    {formatted},")
print("]);")
