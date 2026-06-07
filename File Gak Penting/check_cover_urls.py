import requests
import json

print("Fetching drama data...\n")

response = requests.get(
    'https://tender-connection-production-246f.up.railway.app/api/r2-dramas'
)

dramas = response.json()['dramas']

print(f"Checking first 10 dramas for cover URL format:\n")

for i, drama in enumerate(dramas[:10]):
    title = drama['title']
    cover_url = drama.get('cover_url', 'MISSING')
    
    print(f"{i+1}. {title}")
    print(f"   Cover URL: {cover_url}")
    print(f"   Full URL: {'Yes' if cover_url.startswith('http') else 'NO - Relative path!'}\n")
