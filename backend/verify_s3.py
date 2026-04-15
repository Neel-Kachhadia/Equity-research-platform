from dotenv import load_dotenv
load_dotenv('.env', override=True)
import os, boto3, json
from botocore.config import Config

key    = os.getenv('AWS_SECRET_ACCESS_KEY', '')
aid    = os.getenv('AWS_ACCESS_KEY_ID', '')
region = os.getenv('AWS_REGION', 'ap-south-1').strip()
bucket = os.getenv('S3_BUCKET_NAME', 'itsector1')
prefix = os.getenv('S3_COMPANY_PREFIX', 'companies/')

client = boto3.client(
    's3',
    aws_access_key_id=aid,
    aws_secret_access_key=key,
    region_name=region,
    config=Config(
        retries={'max_attempts': 2, 'mode': 'standard'},
        connect_timeout=3,
        read_timeout=6,
    )
)

print(f"Bucket  : {bucket}")
print(f"Prefix  : {prefix}")
print()

# Test 1: probe_s3 style — list all objects (requires s3:ListBucket)
print("=== Test 1: ListObjectsV2 ===")
try:
    r = client.list_objects_v2(Bucket=bucket, MaxKeys=20)
    objs = r.get('Contents', [])
    if objs:
        print(f"PASS — {len(objs)} object(s) in bucket:")
        for o in objs:
            print(f"  {o['Key']}")
    else:
        print("PASS (bucket is empty)")
except Exception as e:
    print(f"FAIL: {e}")

print()

# Test 2: try to GET a known company JSON
for company in ["TCS", "RELIANCE", "INFY"]:
    s3_key = f"{prefix}{company}.json"
    print(f"=== Test 2: GetObject {s3_key} ===")
    try:
        obj = client.get_object(Bucket=bucket, Key=s3_key)
        body = obj['Body'].read()
        data = json.loads(body)
        print(f"PASS — {len(body)} bytes, keys: {list(data.keys())}")
        break
    except client.exceptions.NoSuchKey:
        print(f"NOT FOUND — {s3_key} does not exist yet")
    except Exception as e:
        code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
        print(f"FAIL [{code}]: {e}")
    print()
