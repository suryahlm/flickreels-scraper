import os
import sys
from datetime import datetime

# Find upload log file
log_files = []
for name in os.listdir('.'):
    if 'upload' in name.lower() and name.endswith('.log'):
        log_files.append(name)

if log_files:
    latest_log = max(log_files, key=lambda f: os.path.getmtime(f))
    print(f"Reading: {latest_log}")
    print("=" * 60)
    with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print(''.join(lines[-50:]))  # Last 50 lines
else:
    print("No upload log files found")
    print("\nTrying to check running process output...")
    
# Check for upload summary
summaries = [f for f in os.listdir('.') if 'summary' in f.lower()]
if summaries:
    print("\n" + "=" * 60)
    print("Upload Summaries:")
    for s in summaries:
        print(f"\n{s}:")
        with open(s, 'r', encoding='utf-8') as f:
            print(f.read())
