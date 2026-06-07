import requests
r = requests.get('https://tender-connection-production-246f.up.railway.app/api/r2-dramas')
dramas = r.json().get('dramas', [])

print("Updated episode counts from API:")
for d in dramas[:15]:
    title = d.get('title', '')[:45]
    eps = d.get('total_episodes', 0)
    print(f"  {eps:3d} eps | {title}")
