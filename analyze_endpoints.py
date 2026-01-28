"""
Script untuk analisis lengkap endpoint FlickReels
"""
import json

with open('API/1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

# ========================================
# 1. Analisis /app/playlet/forYou (Drama List)
# ========================================
print("=" * 80)
print("1. ENDPOINT: /app/playlet/forYou (Drama List)")
print("=" * 80)

for e in entries:
    if '/app/playlet/forYou' in e['request']['url']:
        # Request Body
        if 'postData' in e['request']:
            body = json.loads(e['request']['postData'].get('text', '{}'))
            print("\nREQUEST BODY:")
            print(json.dumps(body, indent=2))
        
        # Response
        resp = e['response']['content'].get('text', '')
        if resp:
            data = json.loads(resp)
            print("\nRESPONSE STRUCTURE:")
            print(f"status_code: {data.get('status_code')}")
            print(f"msg: {data.get('msg')}")
            if 'data' in data and len(data['data']) > 0:
                first_group = data['data'][0]
                print(f"\nFirst group keys: {first_group.keys()}")
                if 'list' in first_group and len(first_group['list']) > 0:
                    print("\nSample drama object:")
                    print(json.dumps(first_group['list'][0], indent=2, ensure_ascii=False))
        break

# ========================================
# 2. Analisis /app/playlet/chapterList (Episode List)
# ========================================
print("\n" + "=" * 80)
print("2. ENDPOINT: /app/playlet/chapterList (Episode List)")
print("=" * 80)

for e in entries:
    if '/app/playlet/chapterList' in e['request']['url']:
        # Request Body
        if 'postData' in e['request']:
            body = json.loads(e['request']['postData'].get('text', '{}'))
            print("\nREQUEST BODY:")
            print(json.dumps(body, indent=2))
        
        # Response
        resp = e['response']['content'].get('text', '')
        if resp:
            data = json.loads(resp)
            print("\nRESPONSE STRUCTURE:")
            print(f"status_code: {data.get('status_code')}")
            if 'data' in data and len(data['data']) > 0:
                print(f"Total episodes: {len(data['data'])}")
                print("\nSample episode object:")
                print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
        break

# ========================================
# 3. Analisis /app/playlet/play (Stream URL)
# ========================================
print("\n" + "=" * 80)
print("3. ENDPOINT: /app/playlet/play (Stream URL)")
print("=" * 80)

for e in entries:
    if '/app/playlet/play' in e['request']['url'] and '/playCheck' not in e['request']['url']:
        # Request Body
        if 'postData' in e['request']:
            body = json.loads(e['request']['postData'].get('text', '{}'))
            print("\nREQUEST BODY:")
            print(json.dumps(body, indent=2))
        
        # Response
        resp = e['response']['content'].get('text', '')
        if resp:
            data = json.loads(resp)
            print("\nRESPONSE STRUCTURE:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
        break

# ========================================
# 4. Headers dari salah satu request
# ========================================
print("\n" + "=" * 80)
print("4. SAMPLE HEADERS (from /app/playlet/forYou)")
print("=" * 80)

for e in entries:
    if '/app/playlet/forYou' in e['request']['url']:
        headers = {h['name']: h['value'] for h in e['request']['headers']}
        for k, v in headers.items():
            print(f"{k}: {v}")
        break
