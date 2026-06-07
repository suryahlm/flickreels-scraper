"""Check what's in Supabase and R2 for Menikah drama"""
import requests
import boto3

SUPABASE_URL = 'https://bmryonqbddbkjbtquhgu.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtcnlvbnFiZGRia2pidHF1aGd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODc2ODQsImV4cCI6MjA4NTI2MzY4NH0.C8Y_kNVDfDvUjdI2HFRDDmybX4yCm7XklaA204kTwMQ'

# Check Supabase
resp = requests.get(
    f'{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.533&select=title,thumbnail_url',
    headers={'apikey': SUPABASE_KEY}
)
print('SUPABASE:')
for d in resp.json():
    print(f"  Title: {d['title']}")
    print(f"  URL: {d['thumbnail_url']}")

# Check R2
s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

print('\nR2 COVER FILES:')
result = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix='flickreels/Menikah lagi dengan Ketua Direksi(Dubbing) (533)/cover')
for obj in result.get('Contents', []):
    head = s3.head_object(Bucket='asiandrama-cdn', Key=obj['Key'])
    print(f"  {obj['Key']} - {head['ContentLength']/1024:.1f}KB")

# Test the Railway stream URL
print('\nTEST RAILWAY STREAM:')
test_url = "https://tender-connection-production-246f.up.railway.app/api/stream/flickreels/Menikah%20lagi%20dengan%20Ketua%20Direksi(Dubbing)%20(533)/cover.png"
test_resp = requests.head(test_url, timeout=30)
print(f"  URL: {test_url[:80]}...")
print(f"  Status: {test_resp.status_code}")
print(f"  Content-Type: {test_resp.headers.get('Content-Type', 'N/A')}")
print(f"  Content-Length: {test_resp.headers.get('Content-Length', 'N/A')}")
