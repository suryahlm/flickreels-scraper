"""
FlickReels Sign Generator
=========================
Implementasi algoritma sign FlickReels berdasarkan decompile APK (class sb.b)

SECRET KEY: tsM5SnqFayhX7c2HfRxm
ALGORITHM: HmacSHA256

Formula:
sign = HmacSHA256(d(body) + "_" + timestamp + "_" + nonce + "_" + b(d(body)), key)

Where:
- d(body) = sorted body string in format: key1_value1_key2_value2_...
- b(string) = r0.c(string) - kemungkinan MD5 hash (perlu konfirmasi)
"""

import hashlib
import hmac
import json
from typing import Any, Dict, List, Union

# SECRET KEY found in APK (class sb.b)
SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"

def method_d(body_json: str) -> str:
    """
    Port dari Java method d(String str):
    - Parse JSON ke dict
    - Sort by key (TreeMap behavior)
    - Format: key1_value1_key2_value2_...
    """
    if not body_json or body_json == "{}":
        return ""
    
    try:
        data = json.loads(body_json)
    except:
        return ""
    
    # Sort by key (TreeMap behavior)
    sorted_data = dict(sorted(data.items()))
    
    parts = []
    for key, value in sorted_data.items():
        if value is not None:
            # Handle nested List or Dict
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value, separators=(',', ':'))
            else:
                value_str = str(value)
            parts.append(f"{key}_{value_str}")
    
    return "_".join(parts)


def method_b(string: str) -> str:
    """
    Port dari Java method b(String str):
    Memanggil r0.c(str) - kemungkinan MD5 hash
    
    TODO: Konfirmasi dengan melihat class kc.r0
    """
    # Assumption: r0.c adalah MD5 hash
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def method_e(message: str, key: str) -> str:
    """
    Port dari Java method e(String str, String str2):
    - HmacSHA256(message, key)
    - Return hex string
    """
    mac = hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    return mac.hexdigest()


def generate_sign(body: Dict[str, Any], timestamp: str, nonce: str) -> str:
    """
    Port dari Java method f(String str, String str2, String str3):
    
    Args:
        body: Request body as dict
        timestamp: Unix timestamp as string
        nonce: Random nonce string (32 chars)
    
    Returns:
        Sign string (64 char hex)
    """
    # Convert body to JSON string (compact, no spaces)
    body_json = json.dumps(body, separators=(',', ':'))
    
    # Method d: process body
    str_d = method_d(body_json)
    
    # Method b: hash of d(body)
    str_b = method_b(str_d)
    
    # Build message: d(body) + "_" + timestamp + "_" + nonce + "_" + b(d(body))
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    
    # Generate HMAC-SHA256
    sign = method_e(message, SECRET_KEY)
    
    return sign


# =============================================================================
# TEST with captured data
# =============================================================================

if __name__ == "__main__":
    # Data dari HTTP Toolkit capture
    CAPTURED = {
        "sign": "9330d1cf8e5ba6bebe216438db99ade8a8765cf04d02ebe7c72625b94131ab27",
        "timestamp": "1769628560",
        "nonce": "FL2Eh26gChwq2w3ANfnGWLKjsiuuND9G",
        "body": {
            "main_package_id": 100,
            "googleAdId": "",
            "device_id": "c3a505a697d0fe79",
            "device_sign": "8ebe44e203712dd92f196ac1e1739e61f32563b7037e24c5d3c2a821296f3e2b",
            "apps_flyer_uid": "1769627657327-1395069204214370834",
            "os": "android",
            "device_brand": "Google",
            "device_number": "16",
            "device_model": "sdk_gphone64_x86_64",
            "language_id": "1",
            "countryCode": ""
        }
    }
    
    print("=" * 60)
    print("FlickReels Sign Generator - Test")
    print("=" * 60)
    print(f"\nSecret Key: {SECRET_KEY}")
    print(f"Expected Sign: {CAPTURED['sign']}")
    print()
    
    # Generate sign
    body_json = json.dumps(CAPTURED['body'], separators=(',', ':'))
    str_d = method_d(body_json)
    str_b = method_b(str_d)
    
    print(f"d(body): {str_d[:80]}...")
    print(f"b(d(body)): {str_b}")
    print()
    
    message = f"{str_d}_{CAPTURED['timestamp']}_{CAPTURED['nonce']}_{str_b}"
    print(f"Message (first 100 chars): {message[:100]}...")
    print()
    
    generated_sign = generate_sign(CAPTURED['body'], CAPTURED['timestamp'], CAPTURED['nonce'])
    print(f"Generated Sign: {generated_sign}")
    
    if generated_sign == CAPTURED['sign']:
        print("\n✅ MATCH! Algoritma benar!")
    else:
        print("\n❌ NOT MATCH - perlu cek method b() (r0.c)")
        print("   Kemungkinan b() bukan MD5, coba lihat class kc.r0")
