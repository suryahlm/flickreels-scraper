import requests,json,time,hashlib,hmac,random,string,boto3
from botocore.config import Config

creds = json.load(open('flickreels_credentials.json'))

r2 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4'))

existing_ids = set()
for page in r2.get_paginator('list_objects_v2').paginate(Bucket='asiandrama-cdn', Prefix='flickreels/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        folder = prefix['Prefix']
        if '(' in folder and ')' in folder:
            existing_ids.add(folder.split('(')[-1].replace(')', '').replace('/', ''))

# API
BASE='https://api.farsunpteltd.com'
SECRET='tsM5SnqFayhX7c2HfRxm'
TOKEN = creds['token']

def nonce():
    return ''.join(random.choices(string.ascii_letters+string.digits,k=32))

def sign(body,ts,n):
    d='_'.join([f'{k}_{v}'for k,v in sorted(body.items())])
    b=hashlib.md5(d.encode()).hexdigest()
    return hmac.new(SECRET.encode(),(f'{d}_{ts}_{n}_{b}').encode(),hashlib.sha256).hexdigest()

# Search for Indonesian dramas by checking random IDs
print("Searching for Indonesian dramas not in R2...")
indonesian_words = ['yang', 'dan', 'aku', 'kau', 'dia', 'itu', 'ini', 'untuk', 'dengan', 'tidak', 'bisa', 'hati', 'cinta']

# Try random high IDs that might be Indonesian
test_ids = [str(i) for i in range(5300, 5400)]  # Recent dramas

found = []
for drama_id in test_ids:
    if drama_id in existing_ids:
        continue
    BODY={
        'main_package_id':100,
        'device_id': creds['device_id'],
        'device_sign': creds['device_sign'],
        'os':'android',
        'language_id':'6',  # Indonesian
        'playlet_id': drama_id
    }
    ts=str(int(time.time()))
    n=nonce()
    headers={'version':'2.2.3.0','token':TOKEN,'sign':sign(BODY,ts,n),'timestamp':ts,'nonce':n,'content-type':'application/json'}
    
    try:
        r=requests.post(BASE+'/app/playlet/chapterList',json=BODY,headers=headers,timeout=10)
        data=r.json()
        if data.get('status_code')==1:
            d = data.get('data',{})
            title = d.get('title','')
            eps = len(d.get('list',[]))
            # Check if title looks Indonesian
            if any(word in title.lower() for word in indonesian_words) or title[0].isupper():
                found.append((drama_id, title, eps))
                print(f"  Found: ID={drama_id}, Title={title}, Episodes={eps}")
                if len(found) >= 3:
                    break
    except:
        pass

if found:
    print(f"\n✅ Found {len(found)} potential Indonesian dramas")
else:
    print("\n⚠️ No new Indonesian dramas found in range")
