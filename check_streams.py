"""
Quick check for stream URLs in HAR
"""
import json

with open('API/1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

print("=== Looking for /app/playlet/play entries ===\n")
count = 0
for e in entries:
    url = e['request']['url']
    if '/app/playlet/play' in url:
        # Skip playCheck and playLimit
        if 'playCheck' in url or 'playLimit' in url:
            continue
        count += 1
        print(f"Entry #{count}: {url}")
        resp = e['response']['content'].get('text', '')
        if resp:
            try:
                data = json.loads(resp)
                status = data.get('status_code')
                print(f"  Status: {status}")
                if status == 1 and data.get('data'):
                    d = data['data']
                    hls = d.get('hls', 'N/A')
                    print(f"  HLS URL: {hls}")
                    print(f"  Title: {d.get('title', 'N/A')}")
            except Exception as ex:
                print(f"  Error parsing: {ex}")
        print()

print(f"\nTotal /app/playlet/play entries: {count}")
