"""
S3 CSV probe script — lists bucket contents and reads the CSV to validate structure.
Run from: python backend/probe_s3.py
"""

import sys, os
import json
import csv
import io
import boto3
import dotenv
from pathlib import Path

# Load .env
dotenv_path = Path(__file__).parent / ".env"
if dotenv_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)

AWS_KEY    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
BUCKET     = os.getenv("S3_BUCKET_NAME", "itsector1")

print(f"Connecting to S3 bucket: s3://{BUCKET}  (region: {AWS_REGION})")
print(f"Key configured: {'YES' if AWS_KEY else 'NO'}")
print()

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name=AWS_REGION,
)

# ── Step 1: List all objects ──────────────────────────────────────────────────
print("=== BUCKET CONTENTS ===")
try:
    paginator = s3.get_paginator("list_objects_v2")
    all_objects = []
    for page in paginator.paginate(Bucket=BUCKET):
        for obj in page.get("Contents", []):
            all_objects.append(obj)
            print(f"  {obj['Key']:60s}  {obj['Size']:>10,} bytes  {obj['LastModified'].strftime('%Y-%m-%d %H:%M')}")

    if not all_objects:
        print("  (bucket is empty)")
        sys.exit(0)

except Exception as e:
    print(f"ERROR listing bucket: {e}")
    sys.exit(1)

# ── Step 2: Find CSV files ────────────────────────────────────────────────────
csv_keys = [o["Key"] for o in all_objects if o["Key"].lower().endswith(".csv")]
print(f"\nFound {len(csv_keys)} CSV file(s):")
for k in csv_keys:
    print(f"  {k}")

if not csv_keys:
    print("No CSV files found. Check bucket path / file extension.")
    sys.exit(1)

# ── Step 3: Read first CSV and preview structure ───────────────────────────────
target = csv_keys[0]
print(f"\n=== READING {target} ===")

try:
    obj = s3.get_object(Bucket=BUCKET, Key=target)
    raw = obj["Body"].read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)

    print(f"Columns ({len(reader.fieldnames)}): {list(reader.fieldnames)}")
    print(f"Total rows: {len(rows)}")
    print()
    print("--- FIRST 3 ROWS (preview) ---")
    for i, row in enumerate(rows[:3]):
        print(json.dumps(dict(row), indent=2, default=str))

except Exception as e:
    print(f"ERROR reading CSV: {e}")
    sys.exit(1)
