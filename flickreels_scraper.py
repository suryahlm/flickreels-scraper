"""
FlickReels API Scraper
======================
Script Python untuk scraping konten dari FlickReels (com.zyhwplatform.shortplay)

Hasil analisis HAR file:
- Base URL: https://api.farsunpteltd.com
- CDN URL (images): https://zshipubcdn.farsunpteltd.com
- CDN URL (streams): https://zshipricf.farsunpteltd.com

Security:
- Menggunakan sign (HMAC-SHA256), timestamp, nonce, dan JWT token
- Sign digenerate dari: sorted JSON body + timestamp + nonce + secret_key
- Token adalah JWT yang diterima saat login (valid selama beberapa waktu)

NOTE: Token yang digunakan di sini diambil dari HAR capture. 
      Untuk penggunaan jangka panjang, perlu implementasi login flow.
"""

import requests
import hashlib
import hmac
import time
import string
import random
import json
from typing import Optional, List, Dict, Any

# ==============================================================================
# CONFIGURATION
# ==============================================================================

BASE_URL = "https://api.farsunpteltd.com"

# Headers yang diambil dari HAR capture
DEFAULT_HEADERS = {
    "version": "2.2.3.0",
    "user-agent": "MyUserAgent",
    "cache-control": "no-cache",
    "content-type": "application/json; charset=UTF-8",
    "accept-encoding": "gzip"
}

# Token JWT VIP dari HTTP Toolkit capture
# Ini adalah token dengan akses VIP untuk streaming semua episode
SAMPLE_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJfIiwiYXVkIjoiXyIsImlhdCI6MTc2OTYyMTU4OCwiZGF0YSI6eyJtZW1iZXJfaWQiOjQ3Mzc5NTE5LCJwYWNrYWdlX2lkIjoiMiIsIm1haW5fcGFja2FnZV9pZCI6MTAwfX0.2a4S7aMATK5f8yWU2QH1rIMMdwoshSyts89CL_i9AQU"

# Default body parameters
DEFAULT_BODY_PARAMS = {
    "main_package_id": 100,
    "googleAdId": "783978b6-0d30-438d-a58d-faf171eed978",  # Sample, bisa random
    "device_id": "0d209b4d4009b44c",
    "device_sign": "9c9ac800ed0e04784ea08c32fdff1406b81400962db3690c6e917bbf4cd361f0",
    "apps_flyer_uid": "1769621528308-5741215934785896746",
    "os": "android",
    "device_brand": "samsung",
    "device_number": "9",
    "device_model": "SM-X710N",
    "language_id": "6",  # 6 = Indonesian
    "countryCode": "ID"
}

# ==============================================================================
# SECURITY: Sign Generation (Reverse Engineered from APK class sb.b)
# ==============================================================================

# SECRET KEY from APK decompile (class sb.b method f)
SIGN_SECRET_KEY = "tsM5SnqFayhX7c2HfRxm"


def generate_nonce(length: int = 32) -> str:
    """Generate random nonce string (matches Java method c)."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def _method_d(body_json: str) -> str:
    """
    Port dari Java method d(String str) di class sb.b:
    - Parse JSON ke dict
    - Sort by key (TreeMap behavior)
    - Format: key1_value1_key2_value2_...
    
    PENTING: Java boolean adalah lowercase (true/false),
    sementara Python adalah Title case (True/False).
    Perlu konversi agar sign cocok.
    """
    if not body_json or body_json == "{}":
        return ""
    
    try:
        data = json.loads(body_json)
    except:
        return ""
    
    # Sort by key (TreeMap behavior in Java)
    sorted_data = dict(sorted(data.items()))
    
    parts = []
    for key, value in sorted_data.items():
        if value is not None:
            # Handle different types to match Java behavior
            if isinstance(value, bool):
                # Java: true/false (lowercase)
                value_str = "true" if value else "false"
            elif isinstance(value, (list, dict)):
                # Nested JSON
                value_str = json.dumps(value, separators=(',', ':'))
            else:
                value_str = str(value)
            parts.append(f"{key}_{value_str}")
    
    return "_".join(parts)


def generate_sign(body: dict, timestamp: int, nonce: str, secret_key: str = SIGN_SECRET_KEY) -> str:
    """
    Generate signature untuk request API FlickReels.
    
    Algoritma (dari APK class sb.b method f):
    -----------------------------------------
    sign = HmacSHA256(
        message = d(body) + "_" + timestamp + "_" + nonce + "_" + md5(d(body)),
        key = "tsM5SnqFayhX7c2HfRxm"
    )
    
    Where d(body) = sorted body string format: key1_value1_key2_value2_...
    
    Args:
        body: Request body as dict
        timestamp: Unix timestamp
        nonce: Random 32-char string
        secret_key: HMAC key (default from APK)
    
    Returns:
        64-char hex string (HMAC-SHA256)
    """
    # Convert body to JSON (compact, no spaces)
    body_json = json.dumps(body, separators=(',', ':'))
    
    # Method d: process body to sorted string
    str_d = _method_d(body_json)
    
    # Method b: MD5 hash of d(body)
    str_b = hashlib.md5(str_d.encode('utf-8')).hexdigest()
    
    # Build message: d(body) + "_" + timestamp + "_" + nonce + "_" + md5(d(body))
    message = f"{str_d}_{timestamp}_{nonce}_{str_b}"
    
    # Generate HMAC-SHA256
    sign = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return sign


# ==============================================================================
# API CLIENT CLASS
# ==============================================================================

class FlickReelsAPI:
    """
    FlickReels API Client.
    
    Usage:
    ------
    api = FlickReelsAPI(token="your_jwt_token")
    dramas = api.get_drama_list()
    episodes = api.get_episodes(playlet_id="894")
    stream_url = api.get_stream_url(playlet_id="894", chapter_id="68993")
    """
    
    def __init__(self, token: str = SAMPLE_TOKEN):
        """
        Initialize API client.
        
        Args:
            token: JWT token untuk autentikasi
        
        Note:
            Sign generation is now fully automated using the reverse-engineered
            algorithm from APK (class sb.b). No need for captured signs anymore!
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
    
    def _make_request(self, endpoint: str, body: dict) -> dict:
        """
        Membuat POST request ke API dengan auto-generated sign.
        
        Args:
            endpoint: Path endpoint (contoh: "/app/playlet/hotRank")
            body: Request body sebagai dictionary
        
        Returns:
            Response JSON sebagai dictionary
        """
        url = f"{BASE_URL}{endpoint}"
        timestamp = int(time.time())
        nonce = generate_nonce()
        
        # Gabungkan body dengan default params
        full_body = {**DEFAULT_BODY_PARAMS, **body}
        
        # Generate sign menggunakan algoritma dari APK (sb.b method f)
        sign = generate_sign(full_body, timestamp, nonce)
        
        # Headers khusus untuk request ini
        headers = {
            "token": self.token,
            "sign": sign,
            "timestamp": str(timestamp),
            "nonce": nonce
        }
        
        try:
            response = self.session.post(
                url, 
                json=full_body, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return {"status_code": -1, "msg": str(e), "data": None}
    
    # ==========================================================================
    # ENDPOINT: Drama List
    # ==========================================================================
    
    def get_drama_list(self, rank_type: int = 1) -> List[Dict[str, Any]]:
        """
        Mendapatkan daftar drama/playlet dari hotRank.
        
        Args:
            rank_type: Tipe ranking (1 = Serial Hot, dll)
        
        Returns:
            List of drama dictionaries dengan fields:
            - playlet_id: ID drama
            - title: Judul drama
            - cover_url: URL gambar cover
            - description: Deskripsi singkat
            - chapter_total: Total episode
            - collection_num: Jumlah koleksi
            - hot_num_text: Teks popularitas
        """
        body = {
            "rank_type": rank_type
        }
        
        result = self._make_request("/app/playlet/hotRank", body)
        
        if result.get("status_code") != 1:
            print(f"[ERROR] Failed to get drama list: {result.get('msg')}")
            return []
        
        dramas = []
        data = result.get("data", [])
        
        for rank_group in data:
            rank_name = rank_group.get("name", "Unknown")
            for item in rank_group.get("data", []):
                dramas.append({
                    "playlet_id": item.get("playlet_id"),
                    "title": item.get("title"),
                    "cover_url": item.get("cover_url"),
                    "description": item.get("description"),
                    "chapter_total": item.get("chapter_total"),
                    "collection_num": item.get("collection_num"),
                    "hot_num_text": item.get("hot_num_split_version"),
                    "rank_name": rank_name,
                    "rank_order": item.get("rank_order")
                })
        
        return dramas
    
    def get_navigation(self) -> List[Dict[str, Any]]:
        """
        Mendapatkan daftar kategori/navigasi.
        
        Returns:
            List of navigation items dengan fields:
            - id: Navigation ID
            - name: Nama kategori
            - home_status: Status home
        """
        result = self._make_request("/app/playlet/navigation", {})
        
        if result.get("status_code") != 1:
            return []
        
        return result.get("data", [])
    
    def get_for_you(self, page_size: int = 20) -> Dict[str, Any]:
        """
        Mendapatkan rekomendasi drama "For You".
        
        Args:
            page_size: Jumlah item per halaman
        
        Returns:
            Dictionary dengan drama recommendations
        """
        body = {
            "page_size": page_size
        }
        
        result = self._make_request("/app/playlet/forYou", body)
        return result.get("data", {})
    
    # ==========================================================================
    # ENDPOINT: Episode/Chapter List
    # ==========================================================================
    
    def get_episodes(self, playlet_id: str, chapter_type: int = -1) -> List[Dict[str, Any]]:
        """
        Mendapatkan daftar episode untuk drama tertentu.
        
        Args:
            playlet_id: ID drama/playlet
            chapter_type: Tipe chapter (-1 untuk semua)
        
        Returns:
            List of episode dictionaries dengan fields:
            - chapter_id: ID episode
            - title: Judul episode
            - chapter_number: Nomor episode
            - duration: Durasi dalam detik
            - is_free: Apakah gratis
            - is_vip: Apakah khusus VIP
            - cover_url: URL thumbnail
        """
        body = {
            "playlet_id": str(playlet_id),
            "chapter_type": chapter_type,
            "auto_unlock": False,
            "fragmentPosition": 0,
            "show_type": 0,
            "source": 1,
            "vip_btn_scene": '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        }
        
        result = self._make_request("/app/playlet/chapterList", body)
        
        if result.get("status_code") != 1:
            print(f"[ERROR] Failed to get episodes: {result.get('msg')}")
            return []
        
        episodes = []
        # Response structure: data.list[] (not data[] directly)
        data = result.get("data", {})
        episode_list = data.get("list", []) if isinstance(data, dict) else data
        
        for ep in episode_list:
            episodes.append({
                "chapter_id": ep.get("chapter_id"),
                "title": ep.get("chapter_title") or ep.get("title"),
                "chapter_number": ep.get("chapter_num") or ep.get("chapter_number"),
                "duration": ep.get("chapter_duration") or ep.get("duration"),
                "is_free": ep.get("is_free", 0) == 1,
                "is_vip": ep.get("is_vip", 0) == 1,
                "is_need_pay": ep.get("is_need_pay", 0) == 1,
                "cover_url": ep.get("chapter_cover") or ep.get("cover_url"),
                "cost_coin": ep.get("cost_coin", 0)
            })
        
        return episodes
    
    # ==========================================================================
    # ENDPOINT: Stream URL (CRITICAL)
    # ==========================================================================
    
    def get_stream_url(self, playlet_id: str, chapter_id: str) -> Optional[str]:
        """
        Mendapatkan URL streaming video (.m3u8) untuk episode tertentu.
        
        Args:
            playlet_id: ID drama/playlet
            chapter_id: ID episode/chapter
        
        Returns:
            URL m3u8 stream, atau None jika gagal
            
        Format URL:
            https://zshipricf.farsunpteltd.com/playlet-hls/hls_{timestamp}_{id}.m3u8?verify={signature}
        """
        body = {
            "playlet_id": str(playlet_id),
            "chapter_id": str(chapter_id),
            "chapter_type": 0,
            "auto_unlock": False,
            "fragmentPosition": 0,
            "show_type": 0,
            "source": 1,
            "vip_btn_scene": '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        }
        
        result = self._make_request("/app/playlet/play", body)
        
        if result.get("status_code") != 1:
            print(f"[ERROR] Failed to get stream URL: {result.get('msg')}")
            return None
        
        data = result.get("data", {})
        
        # URL m3u8 ada di field 'hls_url' atau 'hls'
        stream_url = data.get("hls_url") or data.get("hls")
        
        if stream_url:
            # Tambahan info
            print(f"[INFO] Title: {data.get('playlet_title')} - {data.get('chapter_title')}")
            print(f"[INFO] Duration: {data.get('total_duration')}s")
            print(f"[INFO] VIP Unlock: {data.get('is_vip_unlock')}")
            print(f"[INFO] Play Type: {data.get('e_play_type')}")
            print(f"[INFO] HLS Timeout: {data.get('hls_timeout')}")
            
        return stream_url
    
    def get_play_info(self, playlet_id: str, chapter_id: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi lengkap playback untuk episode tertentu.
        
        Returns:
            Dictionary dengan semua informasi playback:
            - hls: URL stream m3u8
            - title: Judul episode
            - total_duration: Durasi total
            - is_need_pay: Apakah perlu bayar
            - tag_list: Daftar tag/genre
            - dll
        """
        body = {
            "playlet_id": str(playlet_id),
            "chapter_id": str(chapter_id),
            "chapter_type": 0,
            "auto_unlock": False,
            "fragmentPosition": 0,
            "show_type": 0,
            "source": 1,
            "vip_btn_scene": '{"scene_type":[1,3],"play_type":1,"collection_status":0}'
        }
        
        result = self._make_request("/app/playlet/play", body)
        
        if result.get("status_code") != 1:
            return {}
        
        return result.get("data", {})


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def get_drama_list() -> List[Dict[str, Any]]:
    """
    Fungsi convenience untuk mendapatkan daftar drama.
    
    Returns:
        List of drama dictionaries
    """
    api = FlickReelsAPI()
    return api.get_drama_list()


def get_stream_url(playlet_id: str, chapter_id: str) -> Optional[str]:
    """
    Fungsi convenience untuk mendapatkan URL stream.
    
    Args:
        playlet_id: ID drama
        chapter_id: ID episode
    
    Returns:
        URL m3u8 atau None
    """
    api = FlickReelsAPI()
    return api.get_stream_url(playlet_id, chapter_id)


# ==============================================================================
# MAIN - Demo Usage
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FlickReels API Scraper - Demo")
    print("=" * 60)
    
    # Initialize API
    api = FlickReelsAPI(token=SAMPLE_TOKEN)
    
    print("\n[1] Fetching Drama List (Hot Rank)...")
    print("-" * 40)
    dramas = api.get_drama_list()
    
    if dramas:
        print(f"Found {len(dramas)} dramas\n")
        for i, drama in enumerate(dramas[:5]):  # Show first 5
            print(f"{i+1}. [{drama.get('playlet_id')}] {drama.get('title')}")
            print(f"   Episodes: {drama.get('chapter_total')}")
            print(f"   Description: {(drama.get('description') or '')[:50]}...")
            print()
    else:
        print("No dramas found or API request failed")
        print("NOTE: Token mungkin expired. Capture token baru dari HTTP Toolkit.")
    
    # Demo: Get episodes for a specific drama
    if dramas:
        sample_drama_id = dramas[0].get('playlet_id')
        
        print(f"\n[2] Fetching Episodes for Drama ID: {sample_drama_id}...")
        print("-" * 40)
        episodes = api.get_episodes(sample_drama_id)
        
        if episodes:
            print(f"Found {len(episodes)} episodes\n")
            for i, ep in enumerate(episodes[:5]):  # Show first 5
                print(f"  EP.{ep.get('chapter_number')}: [{ep.get('chapter_id')}] {ep.get('title')}")
                print(f"    Duration: {ep.get('duration')}s | Free: {ep.get('is_free')}")
        else:
            print("Failed to get episodes")
        
        # Demo: Get stream URL for first episode
        if episodes:
            sample_chapter_id = episodes[0].get('chapter_id')
            
            print(f"\n[3] Getting Stream URL for Episode ID: {sample_chapter_id}...")
            print("-" * 40)
            stream_url = api.get_stream_url(sample_drama_id, sample_chapter_id)
            
            if stream_url:
                print(f"\n✅ Stream URL:")
                print(stream_url)
                print("\n💡 Gunakan ffmpeg atau VLC untuk memutar URL ini:")
                print(f'   ffmpeg -i "{stream_url}" -c copy output.mp4')
            else:
                print("❌ Failed to get stream URL")
                print("NOTE: Episode mungkin memerlukan VIP atau coin untuk diakses")
    
    print("\n" + "=" * 60)
    print("Demo selesai!")
    print("=" * 60)
