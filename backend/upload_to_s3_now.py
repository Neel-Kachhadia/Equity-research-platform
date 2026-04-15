#!/usr/bin/env python3
"""
upload_to_s3_now.py
===================
Immediately uploads all files already downloaded by the scrapper scripts to S3.
Applies English filter, size filter, and S3 dedup (skips existing keys).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
import boto3

# ── Config ────────────────────────────────────────────────────────────────────
BUCKET       = os.getenv("S3_BUCKET_NAME", "erebus-data-prod")
REGION       = os.getenv("AWS_REGION", "ap-south-1")
SCRAPPER_DIR = Path(__file__).parent.parent / "scrapper"

# Non-English filename filter
NON_ENGLISH = [
    "marathi", "hindi", "gujarati", "tamil", "telugu", "kannada",
    "bengali", "malayalam", "punjabi", "odia", "urdu",
    "-advt", "_advt", "newspaper", "samachar", "vartapatra", "patrika",
    "-notice-hindi", "-notice-marathi", "englist-advt",
]

ALLOWED_EXT = {".pdf", ".csv", ".json", ".xlsx"}
MIN_BYTES   = 10_000   # skip tiny/error files

# ── Company ID mappings (folder name → S3 prefix) ─────────────────────────────
# scrape_indian_companies.py uses these exact IDs as folder names
COMPANY_IDS = {
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM",
    "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK",
    "RELIANCE", "ONGC", "NTPC", "HINDUNILVR", "ITC",
    "TITAN", "ASIANPAINT", "BAJFINANCE", "SUNPHARMA", "DRREDDY",
    "TATASTEEL", "HINDALCO", "TATAMOTORS", "MARUTI", "MM",
}

# indian_investor_documents.py uses different names
LEGACY_NAME_MAP = {
    "TCS": "TCS", "Infosys": "INFY", "HCL_Tech": "HCLTECH",
    "Wipro": "WIPRO", "Tech_Mahindra": "TECHM", "Mindtree": "TECHM",
    "LTTS": "TECHM", "Coforge": "TECHM", "Mphasis": "INFY",
    "Persistent": "INFY",
}

# Category folder → S3 sub-prefix
CATEGORY_MAP = {
    "annual_reports": "Annual_Reports",
    "quarterly_results": "Quarterly_Results",
    "financial_presentations": "Financial_Presentations",
    "other_presentations": "Financial_Presentations",
    "10_year_highlights": "Annual_Reports",
    "csr_reports": "Annual_Reports",
    "other_documents": "Annual_Reports",
    "annual": "Annual_Reports",
    "quarterly": "Quarterly_Results",
    "zipped": None,   # skip zips
}


def is_non_english(name: str) -> bool:
    n = name.lower()
    return any(p in n for p in NON_ENGLISH)


def s3_exists(s3, key: str) -> bool:
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except Exception:
        return False


def upload(s3, local: Path, key: str, stats: dict) -> None:
    if s3_exists(s3, key):
        print(f"  [SKIP] {key}")
        stats["skipped"] += 1
        return
    try:
        s3.upload_file(str(local), BUCKET, key)
        kb = local.stat().st_size // 1024
        print(f"  [OK]   s3://{BUCKET}/{key}  ({kb} KB)")
        stats["uploaded"] += 1
    except Exception as e:
        print(f"  [ERR]  {key}: {e}")
        stats["errors"] += 1


def guess_category(fpath: Path) -> str:
    """Walk up the path looking for a known category folder name."""
    for part in reversed(fpath.parts):
        k = part.lower()
        if k in CATEGORY_MAP:
            return CATEGORY_MAP[k] or ""
    return "Annual_Reports"


def process_tree(s3, root: Path, stats: dict) -> None:
    """Walk a download tree, resolve company + category, upload."""
    for fpath in sorted(root.rglob("*")):
        if not fpath.is_file():
            continue
        if fpath.suffix.lower() not in ALLOWED_EXT:
            continue
        if fpath.stat().st_size < MIN_BYTES:
            continue
        if is_non_english(fpath.name):
            print(f"  [LANG] skip: {fpath.name}")
            continue

        # Resolve company ID from folder hierarchy
        rel = fpath.relative_to(root)
        top = rel.parts[0] if rel.parts else ""

        company_id = None
        if top in COMPANY_IDS:
            company_id = top
        elif top in LEGACY_NAME_MAP:
            company_id = LEGACY_NAME_MAP[top]

        if company_id is None:
            # Try deeper parts
            for part in rel.parts:
                if part in COMPANY_IDS:
                    company_id = part
                    break
                if part in LEGACY_NAME_MAP:
                    company_id = LEGACY_NAME_MAP[part]
                    break

        if company_id is None:
            print(f"  [?CO]  skip (unknown company): {rel}")
            stats["skipped"] += 1
            continue

        cat = guess_category(fpath)
        if not cat:
            print(f"  [?CAT] skip (zip/skip category): {rel}")
            continue

        # Build S3 key: prefix/Category/filename
        s3_key = f"{company_id}/{cat}/{fpath.name}"
        upload(s3, fpath, s3_key, stats)


def main():
    print("=" * 68)
    print("  UPLOAD SCRAPPER OUTPUT -> S3")
    print(f"  Bucket: {BUCKET}   Region: {REGION}")
    print("=" * 68)

    s3 = boto3.client("s3", region_name=REGION)

    stats = {"uploaded": 0, "skipped": 0, "errors": 0}

    # All three scrapper output directories
    trees = [
        SCRAPPER_DIR / "Indian_Companies_Financial_Data",
        SCRAPPER_DIR / "Indian_IT_Companies_Financial_Reports",
        SCRAPPER_DIR / "Indian_IT_Investor_Documents",
    ]

    for tree in trees:
        if not tree.exists():
            print(f"\n[SKIP] {tree.name} — not found yet")
            continue
        count = sum(1 for _ in tree.rglob("*") if _.is_file())
        if count == 0:
            print(f"\n[SKIP] {tree.name} — empty")
            continue
        print(f"\n--- {tree.name}  ({count} files) ---")
        process_tree(s3, tree, stats)

    print()
    print("=" * 68)
    print(f"  Uploaded : {stats['uploaded']}")
    print(f"  Skipped  : {stats['skipped']}  (already in S3 or non-English)")
    print(f"  Errors   : {stats['errors']}")
    print("=" * 68)


if __name__ == "__main__":
    main()
