# FlickReels API Documentation

> Dokumentasi lengkap API FlickReels untuk scraping drama.  
> Generated: 2026-01-29

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Signing](#authentication--signing)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Examples](#requestresponse-examples)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)

---

## Overview

### Base URL
```
https://api.farsunpteltd.com
```

### Package Info
| Property | Value |
|----------|-------|
| App Name | FlickReels |
| Package Name | `com.zyhwplatform.shortplay` |
| Version Tested | 2.2.3.0 |
| Language ID (Indonesia) | 6 |

### Statistics
| Metric | Value |
|--------|-------|
| Total Dramas | **2,376** |
| Valid Navigation IDs | 155 |
| Avg Episodes per Drama | 60-100 |

---

## Authentication & Signing

### Headers Required

Setiap request harus menyertakan headers berikut:

| Header | Description | Example |
|--------|-------------|---------|
| `Token` | JWT token (VIP untuk streaming) | `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...` |
| `Sign` | HMAC-SHA256 signature | `3c9385646fd5f0bc08e8e246eca56afde11a01a8b66572ca...` |
| `Timestamp` | Unix timestamp (seconds) | `1769632577` |
| `Nonce` | 32-character random string | `YfFEMr3gUmWCkzy1fbE3ufHCoXtk0ps6` |
| `Version` | App version | `2.2.3.0` |
| `User-Agent` | Custom UA | `MyUserAgent` |
| `Content-Type` | JSON | `application/json; charset=UTF-8` |

---

### Sign Generation Algorithm

**Secret Key:** `tsM5SnqFayhX7c2HfRxm`

**Algorithm:** HmacSHA256

**Source Code Location:** APK class `sb.b` method `f`

#### Step-by-Step Process

```python
def generate_sign(body: dict, timestamp: str, nonce: str) -> str:
    """
    Generate sign for FlickReels API request.
    
    Args:
        body: Request body as dictionary
        timestamp: Unix timestamp as string
        nonce: 32-character random string
    
    Returns:
        HmacSHA256 signature as hex string
    """
    SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"
    
    # Step 1: Convert body to JSON string (no spaces)
    body_json = json.dumps(body, separators=(',', ':'))
    
    # Step 2: Process body with method_d (sort & format)
    str_d = method_d(body_json)
    
    # Step 3: MD5 hash of str_d
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    
    # Step 4: Construct message
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    
    # Step 5: HmacSHA256
    sign = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return sign
```

#### Method D - Body Processing

```python
def method_d(body_json: str) -> str:
    """
    Process JSON body into sorted key-value string.
    
    Format: key1_value1_key2_value2_...
    
    Special handling:
    - Boolean: Python True/False -> Java true/false (lowercase!)
    - List/Dict: JSON stringify
    - None: Skip
    """
    data = json.loads(body_json)
    sorted_data = dict(sorted(data.items()))
    
    parts = []
    for key, value in sorted_data.items():
        if value is not None:
            if isinstance(value, bool):
                value_str = 'true' if value else 'false'  # CRITICAL: lowercase!
            elif isinstance(value, (list, dict)):
                value_str = json.dumps(value, separators=(',', ':'))
            else:
                value_str = str(value)
            parts.append(f'{key}_{value_str}')
    
    return '_'.join(parts)
```

#### Nonce Generation

```python
def generate_nonce(length: int = 32) -> str:
    """Generate random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))
```

---

### JWT Token Structure

```json
{
  "iss": "_",
  "aud": "_",
  "iat": 1769621588,
  "data": {
    "member_id": 47379519,
    "package_id": "2",
    "main_package_id": 100
  }
}
```

**Note:** Token tidak memiliki field `exp` (expiration), sehingga bisa digunakan dalam jangka panjang. Namun kemungkinan bisa di-revoke oleh server.

---

## API Endpoints

### 1. Navigation Column (Drama List)

**Endpoint:** `POST /app/playlet/navigationColumn`

**Purpose:** Mendapatkan list drama berdasarkan navigation/category ID

**Request Body:**
```json
{
  "navigation_id": 30,
  "page": 1,
  "page_size": 100,
  "main_package_id": 100,
  "device_id": "...",
  "device_sign": "...",
  "os": "android",
  "device_brand": "samsung",
  "device_model": "SM-X710N",
  "language_id": "6",
  "countryCode": "ID"
}
```

**Response:**
```json
{
  "status_code": 1,
  "msg": "成功",
  "data": [
    {
      "column_config_id": 123,
      "nav_id": 281,
      "list": [
        {
          "playlet_id": 4009,
          "title": "Godaan di Malam Hari",
          "cover_url": "https://...",
          "chapter_total": 80,
          "is_vip": 1
        }
      ]
    }
  ]
}
```

**Valid Navigation IDs (Tested):**
```
1, 6, 11, 16, 30, 33, 34, 61, 78, 86, 111, 146, 181, ...
(Total 155 valid IDs in range 1-600)
```

---

### 2. Hot Rank (Trending Dramas)

**Endpoint:** `POST /app/playlet/hotRank`

**Purpose:** Mendapatkan drama trending/populer

**Request Body:**
```json
{
  "rank_type": 0,
  "main_package_id": 100,
  ...
}
```

**Response Structure:**
```json
{
  "status_code": 1,
  "data": [
    {
      "name": "Serial Hot",
      "rank_type": 1,
      "data": [
        {
          "playlet_id": 2858,
          "title": "Tak Bisa Melepasmu",
          "chapter_total": 80
        }
      ]
    }
  ]
}
```

---

### 3. Episode List (Chapter List)

**Endpoint:** `POST /app/playlet/chapterList`

**Purpose:** Mendapatkan daftar episode untuk drama tertentu

**Request Body:**
```json
{
  "playlet_id": "2858",
  "chapter_type": -1,
  "auto_unlock": false,
  "fragmentPosition": 0,
  "show_type": 0,
  "source": 1,
  "vip_btn_scene": "{\"scene_type\":[1,3],\"play_type\":1,\"collection_status\":0}",
  "main_package_id": 100,
  ...
}
```

**Response:**
```json
{
  "status_code": 1,
  "data": {
    "list": [
      {
        "chapter_id": "201356",
        "chapter_title": "Tak Bisa Melepasmu-EP.1",
        "chapter_num": 1,
        "chapter_duration": 158,
        "chapter_cover": "https://...",
        "is_free": 0,
        "is_vip": 1,
        "cost_coin": 0
      }
    ]
  }
}
```

---

### 4. Play (Stream URL)

**Endpoint:** `POST /app/playlet/play`

**Purpose:** Mendapatkan URL streaming HLS (.m3u8) untuk episode

**⚠️ Requires VIP Token untuk episode berbayar**

**Request Body:**
```json
{
  "playlet_id": "2537",
  "chapter_id": "179835",
  "chapter_type": 0,
  "auto_unlock": false,
  "fragmentPosition": 0,
  "show_type": 0,
  "source": 1,
  "vip_btn_scene": "{\"scene_type\":[1,3],\"play_type\":1,\"collection_status\":0}",
  "main_package_id": 100,
  ...
}
```

**Response:**
```json
{
  "status_code": 1,
  "msg": "成功",
  "data": {
    "playlet_id": "2537",
    "chapter_id": "179835",
    "playlet_title": "Nikah Kontrak Berujung Cinta",
    "chapter_title": "Nikah Kontrak Berujung Cinta-EP.67",
    "chapter_num": 67,
    "hls_url": "https://zshipricf.farsunpteltd.com/playlet-hls/1755160303_hls_32311.m3u8?verify=...",
    "hls_time_left": 2400,
    "hls_timeout": 1769634979,
    "is_vip_unlock": 1,
    "e_play_type": "vip",
    "total_duration": 125,
    "tag_list": [
      {"tag_id": 1738, "tag_name": "Cinta Semalam"},
      {"tag_id": 1504, "tag_name": "Romantis"}
    ]
  }
}
```

**Important Fields:**
| Field | Description |
|-------|-------------|
| `hls_url` | URL streaming M3U8 |
| `hls_time_left` | Waktu tersisa sebelum URL expire (seconds) |
| `hls_timeout` | Timestamp kapan URL expire |
| `is_vip_unlock` | 1 jika VIP episode unlocked |
| `e_play_type` | "vip", "free", atau "coin" |

---

### 5. Navigation (Categories)

**Endpoint:** `POST /app/playlet/navigation`

**Purpose:** Mendapatkan list kategori navigasi

**Response:**
```json
{
  "status_code": 1,
  "data": [
    {"navigation_id": null, "name": "home"},
    {"navigation_id": null, "name": "Baru"},
    {"navigation_id": null, "name": "Peringkat"},
    {"navigation_id": null, "name": "Wajib Klasik 🎬"},
    {"navigation_id": null, "name": "Romantis"}
  ]
}
```

---

### 6. Search

**Endpoint:** `POST /app/user_search/search`

**Purpose:** Search drama by keyword

**Request Body:**
```json
{
  "keyword": "cinta",
  "page": 1,
  "page_size": 100,
  ...
}
```

---

### 7. Search Rank List

**Endpoint:** `POST /app/user_search/searchRankList`

**Purpose:** Trending search terms dan drama populer

---

## Request/Response Examples

### Complete Request Example

```http
POST /app/playlet/play HTTP/1.1
Host: api.farsunpteltd.com
Accept-Encoding: gzip
Cache-Control: no-cache
Connection: Keep-Alive
Content-Type: application/json; charset=UTF-8
Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Sign: 3c9385646fd5f0bc08e8e246eca56afde11a01a8b66572ca511db5d78a0ecf18
Timestamp: 1769632577
Nonce: YfFEMr3gUmWCkzy1fbE3ufHCoXtk0ps6
Version: 2.2.3.0
User-Agent: MyUserAgent

{
  "auto_unlock": false,
  "chapter_id": "179835",
  "chapter_type": 0,
  "fragmentPosition": 0,
  "playlet_id": "2537",
  "show_type": 0,
  "source": 1,
  "vip_btn_scene": "{\"scene_type\":[1,3],\"play_type\":1,\"collection_status\":0}",
  "main_package_id": 100,
  "device_id": "0d209b4d4009b44c",
  "device_sign": "3af3b323830984d797d4d623af999126f3ec0d3071f69532c2c4a27b67b89e74",
  "os": "android",
  "device_brand": "samsung",
  "device_number": "9",
  "device_model": "SM-X710N",
  "language_id": "6",
  "countryCode": "ID"
}
```

---

## Error Handling

### Status Codes

| status_code | Meaning |
|-------------|---------|
| `1` | Success |
| `-1` | Error (check `msg` field) |
| `null` | Endpoint not found |

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `签名错误` | Invalid sign | Check sign algorithm, especially boolean casing |
| `token无效` | Invalid/expired token | Get new token from app |
| `无权限` | No permission | VIP required for this content |

---

## Rate Limiting

### Recommendations

| Scenario | Delay |
|----------|-------|
| Sequential requests | 50-100ms |
| Bulk scraping | 100-200ms |
| Avoid detection | 200-500ms + random jitter |

### Tips

1. **Rotate User-Agent** jika membuat banyak request
2. **Cache metadata** - jangan request drama list berulang
3. **Use pagination wisely** - page_size max ~100

---

## CDN Information

### Video Streaming CDN
```
https://zshipricf.farsunpteltd.com/playlet-hls/
```

### Image/Cover CDN
```
https://zshipricf.farsunpteltd.com/playlet/
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial documentation |
| 2026-01-29 | Added 2,376 dramas to database |
| 2026-01-29 | Verified VIP streaming works |

