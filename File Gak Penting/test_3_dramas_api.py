"""
Test API response for 3 specific dramas
"""
import requests
import time

url = f"https://tender-connection-production-246f.up.railway.app/api/r2-dramas?t={int(time.time())}"

print("\n" + "="*60)
print("TESTING API FOR SPECIFIC DRAMAS")
print("="*60)

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    dramas = data['dramas']
    
    search_terms = [
        "Sayang, Aku Benaran Amnesia",
        "Kejayaanku Setelah Berpisah",
        "Istri Kesayangan Mafia"
    ]
    
    for term in search_terms:
        print(f"\n🔍 Searching: {term}")
        found = False
        
        for drama in dramas:
            if term.lower() in drama['title'].lower():
                found = True
                print(f"  ✅ Found: {drama['title']}")
                print(f"     Cover URL: {drama['cover_url']}")
                print(f"     Thumbnail URL: {drama['thumbnail_url']}")
                
                # Test if URL is accessible
                try:
                    cover_response = requests.head(drama['cover_url'], timeout=5)
                    if cover_response.status_code == 200:
                        print(f"     Status: ✅ Accessible (HTTP {cover_response.status_code})")
                    else:
                        print(f"     Status: ❌ HTTP {cover_response.status_code}")
                except Exception as e:
                    print(f"     Status: ❌ Error: {e}")
                break
        
        if not found:
            print(f"  ⚠️  Not found in API response")
    
    print(f"\n{'='*60}\n")
else:
    print(f"❌ API Error: {response.status_code}")
