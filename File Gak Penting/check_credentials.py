#!/usr/bin/env python3
"""
FlickReels Credentials Health Checker
======================================
Validates token and device_sign before scraping.
Alerts user if credentials need refresh.

Usage:
    python check_credentials.py           # Check if credentials valid
    python check_credentials.py --update  # Update credentials interactively
"""
import os
import json
import time
import hashlib
import hmac
import random
import string
import argparse
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "https://api.farsunpteltd.com"
SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"
CREDENTIALS_FILE = "flickreels_credentials.json"

# Current credentials (will be loaded from file or env)
CURRENT_CREDENTIALS = {
    "token": os.getenv("FLICKREELS_TOKEN"),
    "device_sign": "54635c70fbd4b9ece7bcac55af30c6a48a63a8fedcf7f61c4a54cd8604ab4851",
    "device_id": "0d209b4d4009b44c",
    "last_validated": None,
    "last_updated": None,
}

# ============================================================================
# SIGNING
# ============================================================================

def generate_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def method_d(body):
    if not body:
        return ""
    parts = []
    for key, value in sorted(body.items()):
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
    str_d = method_d(body)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    return hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

# ============================================================================
# CREDENTIALS MANAGEMENT
# ============================================================================

def load_credentials():
    """Load credentials from file if exists"""
    global CURRENT_CREDENTIALS
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            saved = json.load(f)
            CURRENT_CREDENTIALS.update(saved)
            print(f"✅ Loaded credentials from {CREDENTIALS_FILE}")
    except FileNotFoundError:
        print(f"⚠️ No saved credentials file, using defaults")
    
    # Override with env if available
    if os.getenv("FLICKREELS_TOKEN"):
        CURRENT_CREDENTIALS["token"] = os.getenv("FLICKREELS_TOKEN")

def save_credentials():
    """Save credentials to file"""
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(CURRENT_CREDENTIALS, f, indent=2)
    print(f"✅ Saved credentials to {CREDENTIALS_FILE}")

def validate_credentials():
    """Test if current credentials work"""
    print("\n🔍 Validating credentials...")
    
    if not CURRENT_CREDENTIALS["token"]:
        print("❌ No token set!")
        return False, "NO_TOKEN"
    
    body = {
        "main_package_id": 100,
        "device_id": CURRENT_CREDENTIALS["device_id"],
        "device_sign": CURRENT_CREDENTIALS["device_sign"],
        "os": "android",
        "language_id": "6",
    }
    
    timestamp = str(int(time.time()))
    nonce = generate_nonce()
    sign = generate_sign(body, timestamp, nonce)
    
    headers = {
        "version": "2.2.3.0",
        "token": CURRENT_CREDENTIALS["token"],
        "sign": sign,
        "timestamp": timestamp,
        "nonce": nonce,
        "content-type": "application/json; charset=UTF-8",
    }
    
    try:
        # Test 1: Login stain (validates token)
        r = requests.post(f"{BASE_URL}/app/login/stain", json=body, headers=headers, timeout=15)
        data = r.json()
        
        if data.get("status_code") == 1:
            print("  ✅ Token: VALID")
        elif data.get("status_code") == 1000 or "login" in data.get("msg", "").lower():
            print("  ❌ Token: EXPIRED")
            return False, "TOKEN_EXPIRED"
        elif "cannot be loaded" in data.get("msg", ""):
            print("  ⚠️ Server issue (try again later)")
            return False, "SERVER_ERROR"
        else:
            print(f"  ❌ Token check failed: {data.get('msg')}")
            return False, "TOKEN_INVALID"
        
        # Test 2: Get drama details (validates full flow)
        body2 = {
            "main_package_id": 100,
            "device_id": CURRENT_CREDENTIALS["device_id"],
            "device_sign": CURRENT_CREDENTIALS["device_sign"],
            "os": "android",
            "language_id": "6",
            "playlet_id": "2858",  # Test drama
        }
        timestamp2 = str(int(time.time()))
        nonce2 = generate_nonce()
        sign2 = generate_sign(body2, timestamp2, nonce2)
        
        headers2 = {
            "version": "2.2.3.0",
            "token": CURRENT_CREDENTIALS["token"],
            "sign": sign2,
            "timestamp": timestamp2,
            "nonce": nonce2,
            "content-type": "application/json; charset=UTF-8",
        }
        
        r = requests.post(f"{BASE_URL}/app/playlet/chapterList", json=body2, headers=headers2, timeout=15)
        data = r.json()
        
        if data.get("status_code") == 1:
            title = data.get("data", {}).get("title", "Unknown")
            print(f"  ✅ API Access: VALID (test drama: {title})")
            CURRENT_CREDENTIALS["last_validated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            return True, "OK"
        else:
            print(f"  ❌ API Access failed: {data.get('msg')}")
            return False, "API_ERROR"
            
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        return False, "CONNECTION_ERROR"

def get_token_age():
    """Get age of token from JWT iat field"""
    import base64
    
    token = CURRENT_CREDENTIALS.get("token", "")
    if not token:
        return None
    
    try:
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "=="))
        iat = payload.get("iat")
        if iat:
            age_seconds = time.time() - iat
            return age_seconds / 86400  # Return in days
    except:
        pass
    return None

def show_status():
    """Display current credentials status"""
    print("\n" + "="*60)
    print("FlickReels Credentials Status")
    print("="*60)
    
    # Token info
    token = CURRENT_CREDENTIALS.get("token", "")
    if token:
        print(f"\n📝 Token: {token[:40]}...")
        age = get_token_age()
        if age:
            print(f"   Age: {age:.1f} days old")
            if age > 7:
                print("   ⚠️ Token is getting old, consider refreshing soon")
            elif age > 14:
                print("   🔴 Token is likely expired!")
    else:
        print("\n📝 Token: NOT SET")
    
    # Device sign
    device_sign = CURRENT_CREDENTIALS.get("device_sign", "")
    print(f"\n📱 Device Sign: {device_sign[:20]}...")
    print(f"   Device ID: {CURRENT_CREDENTIALS.get('device_id', 'NOT SET')}")
    
    # Last validated
    last_validated = CURRENT_CREDENTIALS.get("last_validated")
    if last_validated:
        print(f"\n✅ Last Validated: {last_validated}")
    
    print("\n" + "="*60)

def update_credentials():
    """Interactive credential update"""
    print("\n" + "="*60)
    print("Update FlickReels Credentials")
    print("="*60)
    
    print("\n📋 Instructions:")
    print("1. Open HTTP Toolkit on laptop")
    print("2. Connect phone to HTTP Toolkit")
    print("3. Open FlickReels app on phone")
    print("4. Find any request to api.farsunpteltd.com")
    print("5. Copy the values below from the request headers/body\n")
    
    # Update token
    print("Current token:", (CURRENT_CREDENTIALS.get("token") or "NOT SET")[:30] + "...")
    new_token = input("New token (press Enter to keep current): ").strip()
    if new_token:
        CURRENT_CREDENTIALS["token"] = new_token
        print("  ✅ Token updated")
    
    # Update device_sign
    print("\nCurrent device_sign:", CURRENT_CREDENTIALS.get("device_sign", "NOT SET")[:30] + "...")
    new_sign = input("New device_sign (press Enter to keep current): ").strip()
    if new_sign:
        CURRENT_CREDENTIALS["device_sign"] = new_sign
        print("  ✅ Device sign updated")
    
    # Update device_id
    print("\nCurrent device_id:", CURRENT_CREDENTIALS.get("device_id", "NOT SET"))
    new_id = input("New device_id (press Enter to keep current): ").strip()
    if new_id:
        CURRENT_CREDENTIALS["device_id"] = new_id
        print("  ✅ Device ID updated")
    
    CURRENT_CREDENTIALS["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_credentials()
    
    # Validate new credentials
    print("\n🔍 Testing new credentials...")
    valid, error = validate_credentials()
    
    if valid:
        print("\n✅ Credentials validated successfully!")
        print("\n📋 To update Railway, run:")
        print(f'railway variables set FLICKREELS_TOKEN="{CURRENT_CREDENTIALS["token"]}"')
    else:
        print(f"\n❌ Validation failed: {error}")
        print("Please check your credentials and try again")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='FlickReels Credentials Health Checker')
    parser.add_argument('--update', action='store_true', help='Update credentials interactively')
    parser.add_argument('--validate', action='store_true', help='Validate current credentials')
    parser.add_argument('--status', action='store_true', help='Show credentials status')
    args = parser.parse_args()
    
    load_credentials()
    
    if args.update:
        update_credentials()
    elif args.validate:
        valid, error = validate_credentials()
        if valid:
            save_credentials()  # Save with updated validation time
            print("\n✅ All credentials are valid!")
        else:
            print(f"\n❌ Credentials invalid: {error}")
            print("Run: python check_credentials.py --update")
    elif args.status:
        show_status()
    else:
        # Default: show status and validate
        show_status()
        valid, error = validate_credentials()
        
        if valid:
            save_credentials()
            print("\n✅ Ready to scrape!")
        else:
            print(f"\n❌ Credentials need update: {error}")
            print("\n📋 To fix, run:")
            print("python check_credentials.py --update")

if __name__ == "__main__":
    main()
