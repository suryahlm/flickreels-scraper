#!/usr/bin/env python3
"""
FlickReels Auto Token Manager
=============================
Auto-refresh token using Visitor Login + Signature

Based on reverse-engineered FlickReels auth flow:
1. Generate device credentials
2. Call visitor login endpoint
3. Get fresh JWT token
4. Save to file for persistence
"""
import os
import json
import time
import hashlib
import hmac
import random
import string
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "https://api.farsunpteltd.com"
SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"
TOKEN_FILE = "flickreels_token.json"

# Device credentials (persistent)
DEVICE_CONFIG = {
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "main_package_id": 100,
    "os": "android",
    "device_brand": "samsung",
    "device_model": "SM-X710N",
    "device_number": "9",
    "language_id": "6",
    "countryCode": "ID",
}

# ============================================================================
# SIGNATURE GENERATION
# ============================================================================

def generate_nonce(length=32):
    """Generate random alphanumeric nonce"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def method_d(body):
    """Convert body dict to sorted key_value string"""
    if not body:
        return ""
    sorted_items = sorted(body.items())
    parts = []
    for key, value in sorted_items:
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
    """Generate HMAC-SHA256 signature for FlickReels API"""
    str_d = method_d(body)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def make_signed_request(endpoint, extra_body=None):
    """Make a signed request to FlickReels API"""
    body = {**DEVICE_CONFIG, **(extra_body or {})}
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    
    headers = {
        'version': '2.2.3.0',
        'sign': sign,
        'timestamp': timestamp,
        'nonce': nonce,
        'content-type': 'application/json; charset=UTF-8',
        'user-agent': 'MyUserAgent',
    }
    
    response = requests.post(f'{BASE_URL}{endpoint}', json=body, headers=headers, timeout=30)
    return response.json()

# ============================================================================
# TOKEN MANAGEMENT
# ============================================================================

def load_token_from_file():
    """Load token from local file if exists and not expired"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            token = data.get('token')
            created_at = data.get('created_at', 0)
            
            # Check if token is older than 24 hours
            age_hours = (time.time() - created_at) / 3600
            if age_hours < 24:
                print(f"✅ Loaded token from file (age: {age_hours:.1f} hours)")
                return token
            else:
                print(f"⚠️ Token is {age_hours:.1f} hours old, refreshing...")
                return None
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Token file not found or corrupted")
        return None


def save_token_to_file(token):
    """Save token to local file"""
    data = {
        'token': token,
        'created_at': int(time.time())
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Token saved to {TOKEN_FILE}")


def refresh_token_visitor():
    """Get fresh token via Visitor Login"""
    print("\n🔑 Attempting Visitor Login...")
    
    # List of visitor/guest login endpoints to try
    endpoints = [
        '/app/login/visitor',
        '/app/member/visitorLogin',
        '/app/user/visitor/login',
        '/v1/member/visitorLogin',
        '/app/member/guest',
        '/app/login/guest',
    ]
    
    for endpoint in endpoints:
        try:
            print(f"  Trying {endpoint}...")
            result = make_signed_request(endpoint)
            
            status = result.get('status_code')
            msg = result.get('msg', '')
            
            if status == 1:
                # Success! Extract token
                data = result.get('data', {})
                token = data.get('token') or data.get('access_token') or data.get('jwt')
                
                if token:
                    print(f"  ✅ SUCCESS! Got token: {token[:30]}...")
                    save_token_to_file(token)
                    return token
                else:
                    print(f"  ✅ Response OK but no token in data. Keys: {list(data.keys())}")
                    # Maybe token is in top level
                    if 'token' in result:
                        token = result['token']
                        save_token_to_file(token)
                        return token
            else:
                print(f"  ❌ {msg}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return None


def refresh_token_device_register():
    """Alternative: Try device registration flow"""
    print("\n📱 Attempting Device Registration...")
    
    # Generate new device credentials
    new_device_id = ''.join(random.choices('0123456789abcdef', k=16))
    
    endpoints = [
        '/app/device/register',
        '/app/device/init',
        '/app/init/device',
    ]
    
    for endpoint in endpoints:
        try:
            print(f"  Trying {endpoint}...")
            result = make_signed_request(endpoint, {'device_id': new_device_id})
            
            status = result.get('status_code')
            if status == 1:
                data = result.get('data', {})
                token = data.get('token')
                if token:
                    print(f"  ✅ SUCCESS! Got token: {token[:30]}...")
                    save_token_to_file(token)
                    return token
            else:
                print(f"  ❌ {result.get('msg', 'Unknown error')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return None


def get_fresh_token():
    """
    Main function: Get a valid token
    1. Try loading from file
    2. If expired/missing, try visitor login
    3. If that fails, try device registration
    """
    # Step 1: Try loading from file
    token = load_token_from_file()
    if token:
        # Validate token still works
        print("🔍 Validating token...")
        try:
            # Make a simple API call to test
            body = {**DEVICE_CONFIG}
            timestamp = str(int(time.time()))
            nonce = generate_nonce()
            sign = generate_sign(body, timestamp, nonce)
            
            headers = {
                'version': '2.2.3.0',
                'token': token,
                'sign': sign,
                'timestamp': timestamp,
                'nonce': nonce,
                'content-type': 'application/json; charset=UTF-8',
            }
            
            r = requests.post(f'{BASE_URL}/app/common/bootstrap', json=body, headers=headers, timeout=10)
            result = r.json()
            
            if result.get('status_code') == 1:
                print("✅ Token is valid!")
                return token
            elif result.get('status_code') == 1000 or 'login' in result.get('msg', '').lower():
                print("❌ Token is expired, need refresh...")
            else:
                print(f"⚠️ Unexpected response: {result.get('msg')}")
        except Exception as e:
            print(f"⚠️ Validation error: {e}")
    
    # Step 2: Try visitor login
    token = refresh_token_visitor()
    if token:
        return token
    
    # Step 3: Try device registration
    token = refresh_token_device_register()
    if token:
        return token
    
    print("\n" + "="*60)
    print("❌ ALL AUTO-REFRESH METHODS FAILED")
    print("="*60)
    print("\nManual capture required:")
    print("1. Open HTTP Toolkit on phone")
    print("2. Open FlickReels app")
    print("3. Capture any request to api.farsunpteltd.com")
    print("4. Copy the 'token' header value")
    print("5. Run: python auto_token_manager.py --set TOKEN_VALUE")
    
    return None


def set_token_manual(token):
    """Manually set token from command line"""
    save_token_to_file(token)
    print(f"\n✅ Token set manually: {token[:30]}...")
    print(f"💾 Saved to {TOKEN_FILE}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("FlickReels Auto Token Manager")
    print("="*60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--set' and len(sys.argv) > 2:
            set_token_manual(sys.argv[2])
        elif sys.argv[1] == '--validate':
            token = load_token_from_file()
            if token:
                print(f"Current token: {token[:50]}...")
            else:
                print("No valid token found")
        else:
            print("Usage:")
            print("  python auto_token_manager.py          # Auto-refresh token")
            print("  python auto_token_manager.py --set X  # Manually set token")
            print("  python auto_token_manager.py --validate  # Check current token")
    else:
        token = get_fresh_token()
        
        if token:
            print("\n" + "="*60)
            print("✅ TOKEN READY")
            print("="*60)
            print(f"\nToken: {token[:50]}...")
            print(f"\nTo update Railway:")
            print(f'railway variables set FLICKREELS_TOKEN="{token}"')
        else:
            sys.exit(1)
