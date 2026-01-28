"""
FlickReels Sign Algorithm Analyzer
==================================
Mencoba menemukan algoritma sign dengan membandingkan input vs output.

Dari tracer Frida, kita tahu:
- Algoritma: HmacSHA256
- Input: unknown format (kemungkinan body + timestamp + nonce)
- Key: unknown (embedded di APK)

Data dari HTTP Toolkit:
- Sign: 9330d1cf8e5ba6bebe216438db99ade8a8765cf04d02ebe7c72625b94131ab27
- Timestamp: 1769628560
- Nonce: FL2Eh26gChwq2w3ANfnGWLKjsiuuND9G
"""

import hashlib
import hmac
import json

# Data dari capture
CAPTURED_DATA = {
    "sign": "9330d1cf8e5ba6bebe216438db99ade8a8765cf04d02ebe7c72625b94131ab27",
    "timestamp": "1769628560",
    "nonce": "FL2Eh26gChwq2w3ANfnGWLKjsiuuND9G",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyNzc5NCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3MzgzMjc5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.QX1cL2frC1mNex28b-w0na8ExG6nVCVQfrg7g5jr8bk",
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

# Common HMAC keys yang mungkin digunakan
COMMON_KEYS = [
    "secret",
    "key",
    "api_key",
    "flickreels",
    "zyhwplatform",
    "shortplay",
    "farsunpteltd",
    "@FlickReels2024!",
    "FlickReels@2024",
    "shortplay_secret_key",
    "com.zyhwplatform.shortplay",
    # Empty key
    "",
    # Token based
    CAPTURED_DATA["token"][:32],
    CAPTURED_DATA["token"][-32:],
]

def hmac_sha256(key: str, message: str) -> str:
    """Generate HMAC-SHA256 signature"""
    return hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def sha256(message: str) -> str:
    """Generate SHA256 hash"""
    return hashlib.sha256(message.encode('utf-8')).hexdigest()

def try_sign_formats():
    """Try different input formats for sign generation"""
    timestamp = CAPTURED_DATA["timestamp"]
    nonce = CAPTURED_DATA["nonce"]
    body = CAPTURED_DATA["body"]
    expected_sign = CAPTURED_DATA["sign"]
    
    # Different body formats
    body_json_compact = json.dumps(body, separators=(',', ':'))
    body_json_sorted = json.dumps(body, separators=(',', ':'), sort_keys=True)
    body_json_spaced = json.dumps(body)
    
    # Different input combinations
    input_formats = [
        # Format 1: body + timestamp + nonce
        f"{body_json_compact}{timestamp}{nonce}",
        # Format 2: sorted body + timestamp + nonce
        f"{body_json_sorted}{timestamp}{nonce}",
        # Format 3: timestamp + nonce + body
        f"{timestamp}{nonce}{body_json_compact}",
        # Format 4: nonce + timestamp + body
        f"{nonce}{timestamp}{body_json_compact}",
        # Format 5: body|timestamp|nonce
        f"{body_json_compact}|{timestamp}|{nonce}",
        # Format 6: Just body
        body_json_compact,
        body_json_sorted,
        # Format 7: timestamp + body
        f"{timestamp}{body_json_compact}",
        # Format 8: Combined with &
        f"body={body_json_compact}&timestamp={timestamp}&nonce={nonce}",
        # Format 9: body + timestamp
        f"{body_json_sorted}{timestamp}",
    ]
    
    print("=" * 60)
    print("FlickReels Sign Algorithm Analyzer")
    print("=" * 60)
    print(f"\nExpected sign: {expected_sign}")
    print(f"Timestamp: {timestamp}")
    print(f"Nonce: {nonce}")
    print(f"Body (compact): {body_json_compact[:80]}...")
    print()
    
    # Try SHA256 first (no key needed)
    print("--- Testing SHA256 (no key) ---")
    for i, input_str in enumerate(input_formats):
        result = sha256(input_str)
        match = "✓ MATCH!" if result == expected_sign else ""
        if match or i < 5:  # Show first 5 or matches
            print(f"  Format {i+1}: {result[:32]}... {match}")
    
    print("\n--- Testing HMAC-SHA256 with common keys ---")
    for key in COMMON_KEYS[:5]:
        key_display = key[:20] + "..." if len(key) > 20 else key or "(empty)"
        for i, input_str in enumerate(input_formats[:5]):
            result = hmac_sha256(key, input_str)
            match = "✓ MATCH!" if result == expected_sign else ""
            if match:
                print(f"  Key: {key_display}, Format {i+1}: {result} {match}")
    
    print("\n--- Key patterns to look for in APK ---")
    print("  - Search for: 'HmacSHA256', 'Mac.getInstance', 'SecretKeySpec'")
    print("  - Search in classes: *Interceptor*, *Sign*, *Api*, *Request*")
    
    # Print body for reference
    print("\n--- Request Body (formatted) ---")
    print(json.dumps(body, indent=2))
    
    return None

if __name__ == "__main__":
    try_sign_formats()
