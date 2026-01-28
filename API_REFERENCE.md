# FlickReels API - Analisis Reverse Engineering

Hasil analisis dari file `1.har` (HTTP Toolkit capture)

## 📌 Base URLs

| Type | URL |
|------|-----|
| **API Server** | `https://api.farsunpteltd.com` |
| **CDN Images** | `https://zshipubcdn.farsunpteltd.com` |
| **CDN HLS Streams** | `https://zshipricf.farsunpteltd.com` |

## 🔐 Authentication & Security Headers

### Required Headers

| Header | Description | Example |
|--------|-------------|---------|
| `version` | App version | `2.2.3.0` |
| `token` | JWT authentication token | `eyJ0eXAiOiJKV1Q...` |
| `sign` | HMAC signature (SHA256) | 64-char hex string |
| `timestamp` | Unix timestamp | `1769622559` |
| `nonce` | Random 32-char string | `CivJd1HjnqZ7OHPLrOeJS7Ms7L0EgHWY` |
| `content-type` | JSON content | `application/json; charset=UTF-8` |
| `user-agent` | Custom UA | `MyUserAgent` |

### Sign Generation (Belum Sepenuhnya Decoded)

```
Algorithm: HMAC-SHA256 atau SHA256
Input: sorted_json_body + timestamp + nonce + secret_key
Secret Key: Embedded di APK (perlu decompile)
```

> ⚠️ **CATATAN**: Secret key untuk generate `sign` ada di dalam APK. 
> Untuk penggunaan, perlu decompile APK atau gunakan Frida hook.

## 📡 Endpoint Utama

### 1. Drama List - Hot Rank
```
POST /app/playlet/hotRank

Request Body:
{
  "rank_type": 1,
  "main_package_id": 100,
  "device_id": "...",
  "language_id": "6",
  ...
}

Response:
{
  "status_code": 1,
  "data": [
    {
      "name": "Serial Hot",
      "rank_type": 1,
      "data": [
        {
          "playlet_id": "533",
          "title": "Drama Title",
          "cover_url": "https://...",
          "description": "...",
          "chapter_total": 80,
          "rank_order": 1
        }
      ]
    }
  ]
}
```

### 2. Episode List
```
POST /app/playlet/chapterList

Request Body:
{
  "playlet_id": "894",
  "chapter_type": -1,
  "auto_unlock": false,
  "source": 1
}

Response:
{
  "status_code": 1,
  "data": [
    {
      "chapter_id": "68993",
      "title": "Episode 1",
      "chapter_number": 1,
      "duration": 146,
      "is_free": 1,
      "is_vip": 0,
      "cover_url": "..."
    }
  ]
}
```

### 3. Stream URL (PALING PENTING)
```
POST /app/playlet/play

Request Body:
{
  "playlet_id": "894",
  "chapter_id": "68993",
  "chapter_type": 0,
  "auto_unlock": false,
  "source": 1
}

Response:
{
  "status_code": 1,
  "data": {
    "hls": "https://zshipricf.farsunpteltd.com/playlet-hls/hls_xxx.m3u8?verify=...",
    "title": "Episode Title",
    "total_duration": 146,
    "is_need_pay": 0,
    "tag_list": [...]
  }
}
```

## 🎬 Stream URL Format

```
https://zshipricf.farsunpteltd.com/playlet-hls/{hls_name}.m3u8?verify={timestamp}-{signature}
```

Contoh:
```
https://zshipricf.farsunpteltd.com/playlet-hls/hls_1743422396_1_34251.m3u8?verify=1769626259-RkWilbdoshXM5...
```

## 📋 Default Body Parameters

```json
{
  "main_package_id": 100,
  "googleAdId": "783978b6-0d30-438d-a58d-faf171eed978",
  "device_id": "0d209b4d4009b44c",
  "device_sign": "...",
  "apps_flyer_uid": "...",
  "os": "android",
  "device_brand": "samsung",
  "device_number": "9",
  "device_model": "SM-X710N",
  "language_id": "6",
  "countryCode": "ID"
}
```

### Language IDs

| ID | Language |
|----|----------|
| 1 | English |
| 2 | 日本語 (Japanese) |
| 3 | 한국어 (Korean) |
| 4 | 繁體中文 (Traditional Chinese) |
| 5 | Español (Spanish) |
| 6 | Bahasa Indonesia |
| 7 | ภาษาไทย (Thai) |
| 8 | Deutsch (German) |
| 10 | Português (Portuguese) |
| 11 | Français (French) |
| 12 | بالعربية (Arabic) |

## 🔄 Endpoint Lainnya

| Endpoint | Deskripsi |
|----------|-----------|
| `/app/playlet/navigation` | Kategori/tab navigasi |
| `/app/playlet/forYou` | Rekomendasi untuk user |
| `/app/playlet/latestPlay` | Riwayat terakhir diputar |
| `/app/playlet/preload` | Preload data |
| `/app/user_search/getHotKeywordList` | Keyword pencarian populer |
| `/app/signin/index` | Info sign-in reward |
| `/app/my/myWallet` | Info wallet user |
| `/app/my/userInfo` | Info profil user |

## ⚡ Cara Bypass Signature

### Opsi 1: Frida Hook (Recommended)
```javascript
// Hook fungsi sign di runtime
Java.perform(function() {
    var SignUtil = Java.use("com.xxx.SignatureUtil");
    SignUtil.generateSign.implementation = function(body, ts, nonce) {
        console.log("Body: " + body);
        console.log("Timestamp: " + ts);
        console.log("Nonce: " + nonce);
        var result = this.generateSign(body, ts, nonce);
        console.log("Sign: " + result);
        return result;
    };
});
```

### Opsi 2: HTTP Toolkit + Manual Capture
1. Capture request fresh dari app
2. Copy semua headers (`sign`, `timestamp`, `nonce`, `token`)
3. Gunakan headers tersebut dalam waktu singkat (sebelum expired)

### Opsi 3: Decompile APK
1. Extract APK dengan `apktool`
2. Cari class SignatureUtil atau similar
3. Analisis algoritma dan secret key

## 📦 Package Info

| Field | Value |
|-------|-------|
| Package Name | `com.zyhwplatform.shortplay` |
| App Name | FlickReels |
| Version | 2.2.3.0 |
| Version Code | 101167 |
