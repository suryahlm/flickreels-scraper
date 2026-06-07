import requests,json,time,hashlib,hmac,random,string

BASE='https://api.farsunpteltd.com'
SECRET='tsM5SnqFayhX7c2HfRxm'

creds = json.load(open('flickreels_credentials.json'))
TOKEN = creds['token']

BODY={
    'main_package_id':100,
    'device_id': creds['device_id'],
    'device_sign': creds['device_sign'],
    'os':'android',
    'language_id':'6',
    'page':'1',
    'page_size':'20'
}

def nonce():
    return ''.join(random.choices(string.ascii_letters+string.digits,k=32))

def sign(body,ts,n):
    d='_'.join([f'{k}_{v}'for k,v in sorted(body.items())])
    b=hashlib.md5(d.encode()).hexdigest()
    return hmac.new(SECRET.encode(),(f'{d}_{ts}_{n}_{b}').encode(),hashlib.sha256).hexdigest()

ts=str(int(time.time()))
n=nonce()
headers={
    'version':'2.2.3.0',
    'token':TOKEN,
    'sign':sign(BODY,ts,n),
    'timestamp':ts,
    'nonce':n,
    'content-type':'application/json'
}

# Get hot Indonesian dramas
r=requests.post(BASE+'/app/playlet/hotRank',json=BODY,headers=headers,timeout=15)
resp=r.json()
print('Response:', json.dumps(resp, indent=2)[:500])
