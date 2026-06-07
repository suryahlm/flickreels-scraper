"""Investigate cover issues in R2"""
import boto3
import json

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9')

# List all drama folders
result = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix='flickreels/', Delimiter='/')
folders = [p['Prefix'] for p in result.get('CommonPrefixes', [])]

print(f'Found {len(folders)} drama folders\n')

for folder in folders[:5]:  # Check first 5
    folder_name = folder.replace('flickreels/', '').rstrip('/')
    print(f'=== {folder_name} ===')
    
    # Get metadata
    try:
        meta_obj = s3.get_object(Bucket='asiandrama-cdn', Key=f'{folder}metadata.json')
        metadata = json.loads(meta_obj['Body'].read().decode('utf-8'))
        cover = metadata.get('cover', 'N/A')
        cover_r2 = metadata.get('cover_r2', 'N/A')
        print(f'  API cover: {cover[:80]}...' if len(str(cover)) > 80 else f'  API cover: {cover}')
        print(f'  R2 cover path: {cover_r2}')
    except Exception as e:
        print(f'  Metadata error: {e}')
    
    # List cover files in this folder
    cover_result = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=f'{folder}cover', MaxKeys=10)
    covers = [o['Key'].split('/')[-1] for o in cover_result.get('Contents', [])]
    print(f'  Cover files in R2: {covers}')
    print()
