import requests

# Test CDN MP4 URL for the 2 converted dramas
urls = [
    "https://cdn.asiandrama.cc/flickreels/30%20Hari%20untuk%20Merelakanmu%20(2234)/ep_001.mp4",
    "https://cdn.asiandrama.cc/flickreels/7%20Hari%20Panduan%20Bertahan%20Longsor%20(4509)/ep_001.mp4",
]

for url in urls:
    try:
        r = requests.head(url, timeout=10)
        size_mb = int(r.headers.get("content-length", 0)) / 1024 / 1024
        ct = r.headers.get("content-type", "N/A")
        print(f"URL: ...{url[-60:]}")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {ct}")
        print(f"  Size: {size_mb:.1f} MB")
        print()
    except Exception as e:
        print(f"Error: {e}")
