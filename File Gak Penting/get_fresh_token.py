#!/usr/bin/env python3
"""
FlickReels Auto Token Generator
================================
Gets a fresh token using guest login

Usage:
    python get_fresh_token.py
"""
import requests
import json
import time
import hashlib
import hmac
import random
import string

BASE_URL = "https://api.farsunpteltd.com"
SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"

# Device info (can be random)
DEVICE = {
    "main_package_id": 100,
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "countryCode": "ID",
    "language_id": "6"
}

def generate_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def method_d(body_json):
    data = json.loads(body_json)
    sorted_data = dict(sorted(data.items()))
    parts = []
    for key, value in sorted_data.items():
        if value is not None:
            if isinstance(value, bool):
                value_str = 'true' if value else 'false'
            elif isinstance(value, (list, dict)):
                value_str = json.dumps(value, separators=(',', ':'))
            else:
                value_str = str(value)
            parts.append(f'{key}_{value_str}')
    return '_'.join(parts)

def generate_sign(body, timestamp, nonce):
    body_json = json.dumps(body, separators=(',', ':'))
    str_d = method_d(body_json)
    str_b = hashlib.md5(str_d.encode()).hexdigest()
    msg = f'{str_d}_{timestamp}_{nonce}_{str_b}'
    return hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()

def try_login_endpoint(endpoint, extra_body=None):
    """Try a login endpoint and return token if successful"""
    body = {**DEVICE, **(extra_body or {})}
    ts = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, ts, nonce)
    
    headers = {
        'version': '2.2.3.0',
        'sign': sign,
        'timestamp': ts,
        'nonce': nonce,
        'content-type': 'application/json; charset=UTF-8',
        'user-agent': 'MyUserAgent'
    }
    
    try:
        r = requests.post(f'{BASE_URL}{endpoint}', json=body, headers=headers, timeout=15)
        data = r.json()
        print(f"\n{endpoint}")
        print(f"  Status: {data.get('status_code')}")
        print(f"  Msg: {data.get('msg')}")
        
        if data.get('status_code') == 1:
            # Look for token in response
            resp_data = data.get('data', {})
            if isinstance(resp_data, dict):
                token = resp_data.get('token') or resp_data.get('access_token') or resp_data.get('jwt')
                if token:
                    print(f"  ✅ TOKEN FOUND!")
                    return token
                # Print all keys to see what's available
                print(f"  Keys: {list(resp_data.keys())[:10]}")
        return None
    except Exception as e:
        print(f"\n{endpoint}")
        print(f"  Error: {e}")
        return None

def main():
    print("="*60)
    print("FLICKREELS TOKEN SCANNER")
    print("="*60)
    
    # List of potential login endpoints
    endpoints = [
        # Guest login variations
        ("/app/member/guestLogin", {}),
        ("/member/guestLogin", {}),
        ("/v1/member/guestLogin", {}),
        ("/v2/member/guestLogin", {}),
        ("/app/user/guestLogin", {}),
        
        # Device registration
        ("/app/device/register", {}),
        ("/app/member/register", {}),
        
        # Init/startup
        ("/app/init", {}),
        ("/app/startup", {}),
        ("/app/config", {}),
        
        # Token refresh
        ("/app/member/refreshToken", {}),
        ("/app/token/refresh", {}),
    ]
    
    for endpoint, extra in endpoints:
        token = try_login_endpoint(endpoint, extra)
        if token:
            print(f"\n" + "="*60)
            print("SUCCESS! New token:")
            print(token)
            print("\nTo update Railway:")
            print(f'railway variables set FLICKREELS_TOKEN="{token}"')
            return token
    
    print(f"\n" + "="*60)
    print("❌ No token found from any endpoint")
    print("Token harus didapat dari capture app menggunakan proxy/Frida")
    return None

if __name__ == "__main__":
    main()
