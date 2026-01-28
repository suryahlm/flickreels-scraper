"""
Script untuk menganalisis HAR file FlickReels
Ekstraksi endpoint dan struktur data
"""
import json

with open('API/1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

# Find key endpoints
key_endpoints = [
    '/app/playlet/forYou',
    '/app/playlet/hotRank',
    '/app/playlet/chapterList',
    '/app/playlet/play',
    '/app/playlet/navigation',
    '/app/playlet/navigationColumn'
]

for ep in key_endpoints:
    for e in entries:
        if ep in e['request']['url']:
            print(f'\n=== {ep} ===')
            print(f"Method: {e['request']['method']}")
            print(f"URL: {e['request']['url']}")
            
            # Headers
            headers = {h['name']: h['value'] for h in e['request']['headers']}
            custom = ['version', 'sign', 'timestamp', 'nonce', 'token']
            print('Security Headers:')
            for h in custom:
                if h in headers:
                    val = headers.get(h, 'N/A')
                    if len(val) > 60:
                        print(f'  {h}: {val[:60]}...')
                    else:
                        print(f'  {h}: {val}')
            
            # Request Body
            if 'postData' in e['request']:
                body = e['request']['postData'].get('text', '')
                print(f'Request Body (preview): {body[:350]}...')
            
            # Response (preview)
            resp = e['response']['content'].get('text', '')
            if resp:
                print(f'Response (preview): {resp[:500]}...')
            break
