"""
Full connectivity check: S3 + RDS PostgreSQL + ElastiCache Redis
"""
from dotenv import load_dotenv
load_dotenv('.env', override=True)
import os

aid    = os.getenv('AWS_ACCESS_KEY_ID', '')
key    = os.getenv('AWS_SECRET_ACCESS_KEY', '')
region = os.getenv('AWS_REGION', 'ap-south-1').strip()
bucket = os.getenv('S3_BUCKET_NAME', 'itsector1')
db_url = os.getenv('DATABASE_URL', '')
redis_url = os.getenv('REDIS_URL', '')

print("=" * 55)
print("EREBUS Infrastructure Connectivity Check")
print("=" * 55)

# ── 1. S3 ─────────────────────────────────────────────────
print("\n[1/3] S3")
try:
    import boto3
    from botocore.config import Config
    client = boto3.client('s3', aws_access_key_id=aid, aws_secret_access_key=key,
        region_name=region, config=Config(connect_timeout=3, read_timeout=5,
        retries={'max_attempts': 2, 'mode': 'standard'}))
    r = client.list_objects_v2(Bucket=bucket, Prefix='companies/', MaxKeys=5)
    objs = [o['Key'] for o in r.get('Contents', [])]
    print(f"  ✓ Connected to s3://{bucket}")
    if objs:
        print(f"  ✓ Files in companies/: {objs}")
    else:
        print(f"  ⚠ companies/ prefix is empty — need to upload company JSON files")
except Exception as e:
    code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
    print(f"  ✗ FAILED [{code}]: {e}")

# ── 2. RDS PostgreSQL ─────────────────────────────────────
print("\n[2/3] RDS PostgreSQL")
try:
    import psycopg2
    from urllib.parse import urlparse
    p = urlparse(db_url)
    conn = psycopg2.connect(
        host=p.hostname, port=p.port or 5432,
        database=p.path.lstrip('/'),
        user=p.username, password=p.password,
        sslmode='require', connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    cur.close(); conn.close()
    print(f"  ✓ Connected to RDS PostgreSQL")
    print(f"  ✓ {version[:60]}...")
except ImportError:
    print("  ✗ psycopg2 not installed — run: pip install psycopg2-binary")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# ── 3. ElastiCache Redis ──────────────────────────────────
print("\n[3/3] ElastiCache Redis")
try:
    import redis
    r = redis.from_url(redis_url, ssl=True, socket_timeout=5, socket_connect_timeout=3)
    pong = r.ping()
    print(f"  ✓ Connected to ElastiCache Redis — PING: {pong}")
    info = r.info('server')
    print(f"  ✓ Redis version: {info.get('redis_version','?')}")
except ImportError:
    print("  ✗ redis-py not installed — run: pip install redis")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

print("\n" + "=" * 55)
