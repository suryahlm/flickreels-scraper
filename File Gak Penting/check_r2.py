"""
Check R2 folder contents for specific drama
"""
import boto3
from botocore.config import Config

s3 = boto3.client(
    's3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

folder = 'flickreels/1955 Married the Mafia Boss by Contract (1198)/'
print(f'Checking: {folder}')
response = s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=folder, MaxKeys=20)
contents = response.get('Contents', [])
print(f'Files found: {len(contents)}')
for obj in contents[:10]:
    key = obj['Key'].replace(folder, '')
    size = obj['Size']
    print(f'  - {key} ({size} bytes)')
