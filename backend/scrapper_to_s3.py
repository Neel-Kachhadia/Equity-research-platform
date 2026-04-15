#!/usr/bin/env python3
"""
scrapper_to_s3.py
=================
Bridge: runs the existing scrapper/ scripts, then uploads everything to S3.

Steps:
  1. Run scrape_indian_companies.py  -> downloads PDFs per company to
       scrapper/Indian_Companies_Financial_Data/{COMPANY_ID}/...
  2. Run indian_it_financial_extractor.py -> yfinance CSVs + generated PDFs to
       scrapper/Indian_IT_Companies_Financial_Reports/{Name}/...
  3. Walk both output trees, filter non-English & non-PDF, upload to S3.

S3 layout mirrors the backend pipeline:
  {COMPANY_ID}/Annual_Reports/
  {COMPANY_ID}/Quarterly_Results/
  {COMPANY_ID}/Financial_Presentations/
  {COMPANY_ID}/Yahoo_Financials/
"""

import os, sys, re, subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "modules" / ".." / ".env")
load_dotenv(Path(__file__).parent / ".env")

import boto3

# ── Config ────────────────────────────────────────────────────────────────────
BUCKET       = os.getenv("S3_BUCKET_NAME", "erebus-data-prod")
REGION       = os.getenv("AWS_REGION", "ap-south-1")
SCRAPPER_DIR = Path(__file__).parent.parent / "scrapper"

# Map scrapper company IDs → S3 prefix (backend uses these IDs)
COMPANY_ID_MAP = {
    # scrapper id  ->  S3 prefix
    "TCS":         "TCS",
    "INFY":        "INFY",
    "WIPRO":       "WIPRO",
    "HCLTECH":     "HCLTECH",
    "TECHM":       "TECHM",
    "HDFCBANK":    "HDFCBANK",
    "ICICIBANK":   "ICICIBANK",
    "SBIN":        "SBIN",
    "AXISBANK":    "AXISBANK",
    "KOTAKBANK":   "KOTAKBANK",
    "RELIANCE":    "RELIANCE",
    "ONGC":        "ONGC",
    "NTPC":        "NTPC",
    "HINDUNILVR":  "HINDUNILVR",
    "ITC":         "ITC",
    "TITAN":       "TITAN",
    "ASIANPAINT":  "ASIANPAINT",
    "BAJFINANCE":  "BAJFINANCE",
    "SUNPHARMA":   "SUNPHARMA",
    "DRREDDY":     "DRREDDY",
    "TATASTEEL":   "TATASTEEL",
    "HINDALCO":    "HINDALCO",
    "TATAMOTORS":  "TATAMOTORS",
    "MARUTI":      "MARUTI",
    "MM":          "MM",
    # indian_it_financial_extractor names
    "TCS_IT":              "TCS",
    "Infosys":             "INFY",
    "HCL Technologies":    "HCLTECH",
    "Wipro":               "WIPRO",
    "Tech Mahindra":       "TECHM",
}

# Map scrapper category folder → S3 sub-prefix
CATEGORY_S3_MAP = {
    "Annual_Reports":          "Annual_Reports",
    "Quarterly_Results":       "Quarterly_Results",
    "Financial_Presentations": "Financial_Presentations",
    "Other_Presentations":     "Financial_Presentations",
    "10_Year_Highlights":      "Annual_Reports",
    "CSR_Reports":             "Annual_Reports",   # lump with annual for now
    "Other_Documents":         "Annual_Reports",
    "annual":                  "Annual_Reports",
    "quarterly":               "Quarterly_Results",
}

# Non-English filename patterns (same as pdf_scraper.py)
NON_ENGLISH_PATTERNS = [
    "marathi", "hindi", "gujarati", "tamil", "telugu", "kannada",
    "bengali", "malayalam", "punjabi", "odia", "urdu",
    "-advt", "_advt", "newspaper", "samachar", "vartapatra", "patrika",
    "-notice-hindi", "-notice-marathi",
]

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".json", ".xlsx"}


def is_non_english(name: str) -> bool:
    n = name.lower()
    return any(p in n for p in NON_ENGLISH_PATTERNS)


def s3_key_exists(s3, key: str) -> bool:
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False
    except Exception:
        return False


def upload_file(s3, local_path: Path, s3_key: str) -> bool:
    if s3_key_exists(s3, s3_key):
        print(f"  [SKIP] already in S3: {s3_key}")
        return False
    try:
        s3.upload_file(str(local_path), BUCKET, s3_key)
        size_kb = local_path.stat().st_size // 1024
        print(f"  [OK]   s3://{BUCKET}/{s3_key}  ({size_kb} KB)")
        return True
    except Exception as e:
        print(f"  [ERR]  {s3_key}: {e}")
        return False


def guess_category(path: Path) -> str:
    """Infer S3 sub-prefix from the file's folder hierarchy."""
    parts = [p.lower() for p in path.parts]
    for part in reversed(parts):
        if part in {k.lower(): k for k in CATEGORY_S3_MAP}:
            return CATEGORY_S3_MAP.get(part, "Annual_Reports")
        for k, v in CATEGORY_S3_MAP.items():
            if k.lower() in part:
                return v
    return "Annual_Reports"


def infer_company_id(path: Path, root: Path) -> str | None:
    """Try to find the company ID from the path relative to root."""
    rel = path.relative_to(root)
    top = rel.parts[0] if rel.parts else ""
    return COMPANY_ID_MAP.get(top)


def upload_tree(s3, root: Path, uploaded: dict) -> int:
    """Walk a download tree and upload eligible files to S3."""
    count = 0
    for fpath in root.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if is_non_english(fpath.name):
            print(f"  [SKIP-lang] {fpath.name}")
            continue
        if fpath.stat().st_size < 10_000:
            continue  # skip tiny files / error pages

        company_id = infer_company_id(fpath, root)
        if not company_id:
            # Try to guess from parent dir names
            for part in fpath.parts:
                if part in COMPANY_ID_MAP:
                    company_id = COMPANY_ID_MAP[part]
                    break
        if not company_id:
            print(f"  [SKIP-noco] {fpath.relative_to(root)}")
            continue

        category = guess_category(fpath)
        s3_key = f"{company_id}/{category}/{fpath.name}"

        if upload_file(s3, fpath, s3_key):
            uploaded[company_id] = uploaded.get(company_id, 0) + 1
            count += 1
    return count


def run_script(script: Path, cwd: Path, out_dir: Path | None = None):
    if out_dir and out_dir.exists() and any(out_dir.rglob("*")):
        print(f">>> Skip (already ran): {script.name}  (output: {out_dir.name})")
        return
    print(f"\n>>> Running: {script.name}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"   # prevent cp1252 crash on Windows
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(cwd),
        capture_output=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0:
        print(f"    [WARN] {script.name} exited with code {result.returncode}")


def main():
    print("=" * 70)
    print("SCRAPPER -> S3  BRIDGE")
    print("=" * 70)

    s3 = boto3.client("s3", region_name=REGION)
    print(f"S3 bucket: {BUCKET}  region: {REGION}")

    uploaded: dict[str, int] = {}

    # ── Phase 1: Run scrape_indian_companies.py ────────────────────────────
    # This downloads PDFs into scrapper/Indian_Companies_Financial_Data/
    script1 = SCRAPPER_DIR / "scrape_indian_companies.py"
    out_dir1 = SCRAPPER_DIR / "Indian_Companies_Financial_Data"
    if script1.exists():
        run_script(script1, SCRAPPER_DIR, out_dir1)
    else:
        print(f"[SKIP] {script1} not found")

    if out_dir1.exists():
        print(f"\n-- Uploading from {out_dir1.name} --")
        n = upload_tree(s3, out_dir1, uploaded)
        print(f"   Uploaded {n} files from IR scraper")
    else:
        print(f"[WARN] {out_dir1} does not exist — skipping upload")

    # ── Phase 2: Run indian_it_financial_extractor.py ─────────────────────
    # Produces CSVs + generated PDFs in scrapper/Indian_IT_Companies_Financial_Reports/
    script2 = SCRAPPER_DIR / "indian_it_financial_extractor.py"
    out_dir2 = SCRAPPER_DIR / "Indian_IT_Companies_Financial_Reports"
    if script2.exists():
        run_script(script2, SCRAPPER_DIR, out_dir2)
    else:
        print(f"[SKIP] {script2} not found")

    if out_dir2.exists():
        print(f"\n-- Uploading from {out_dir2.name} --")
        n = upload_tree(s3, out_dir2, uploaded)
        print(f"   Uploaded {n} files from yfinance extractor")
    else:
        print(f"[WARN] {out_dir2} does not exist — skipping upload")

    # ── Phase 3: Run indian_investor_documents.py (IT-focused, 10 companies)
    script3 = SCRAPPER_DIR / "indian_investor_documents.py"
    out_dir3 = SCRAPPER_DIR / "Indian_IT_Investor_Documents"
    if script3.exists():
        run_script(script3, SCRAPPER_DIR, out_dir3)
    else:
        print(f"[SKIP] {script3} not found")

    if out_dir3.exists():
        print(f"\n-- Uploading from {out_dir3.name} --")
        n = upload_tree(s3, out_dir3, uploaded)
        print(f"   Uploaded {n} files from IT investor docs scraper")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  UPLOAD SUMMARY")
    print("=" * 70)
    for company, count in sorted(uploaded.items()):
        print(f"  {company:<15}  {count:>3} new files")
    total = sum(uploaded.values())
    print(f"\n  Total new files uploaded: {total}")
    print("=" * 70)


if __name__ == "__main__":
    main()
