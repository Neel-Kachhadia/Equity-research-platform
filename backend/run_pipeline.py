"""
EREBUS · Full Ingestion Run
============================
Runs for a targeted set of companies:
  - Yahoo Finance: price history + financials  -> S3 JSON
  - IR page PDFs: investor-relations scraping  -> S3 PDF
  - BSE/MCA filings: annual + quarterly reports -> S3 PDF

Usage:
    python run_pipeline.py              # all 25 companies
    python run_pipeline.py TCS INFY     # specific companies
"""

# Load .env FIRST before any module reads os.getenv()
import os
from dotenv import load_dotenv
load_dotenv()

import logging
import sys
from datetime import datetime, timezone

from modules.ingestion import (
    run_ingestion_pipeline,
    ALL_COMPANY_IDS,
    get_ticker, get_cin, get_bse_code, get_sector,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main():
    target = sys.argv[1:] if len(sys.argv) > 1 else ALL_COMPANY_IDS

    invalid = [c for c in target if c not in ALL_COMPANY_IDS]
    if invalid:
        print("Unknown company IDs:", invalid)
        print("Valid IDs:", ALL_COMPANY_IDS)
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    bucket = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_S3_BUCKET", "erebus-data-prod")

    sep = "=" * 65
    print()
    print(sep)
    print("  EREBUS - Ingestion Pipeline")
    print("  Companies :", len(target))
    print("  Sources   : Yahoo Finance | IR PDFs | BSE Annual Reports")
    print("  Storage   : S3 (" + bucket + ")")
    print("  Started   :", now, "UTC")
    print(sep)
    print()

    for cid in target:
        bse   = get_bse_code(cid) or "n/a"
        cin   = (get_cin(cid) or "n/a")
        print(f"  {cid:<14} ticker={get_ticker(cid):<15} sector={get_sector(cid):<12}"
              f" bse={bse:<6} cin={cin}")
    print()

    # ── Run ────────────────────────────────────────────────────────────────────
    result = run_ingestion_pipeline(
        company_ids=target,
        fetch_prices=True,   # Yahoo Finance OHLCV + financials
        fetch_pdfs=True,     # IR page PDFs
        fetch_mca=True,      # BSE annual reports + MCA eFiling
        dry_run=False,       # Actually upload to S3
    )

    # ── Report ─────────────────────────────────────────────────────────────────
    print()
    print(sep)
    print("  RESULTS")
    print(sep)
    col = "{:<14} {:>8} {:>10} {:>10}"
    print(col.format("Company", "Prices", "IR PDFs", "MCA/BSE"))
    print("-" * 46)

    for cid, d in result.details.items():
        prices = d.get("prices") or {}
        ir     = d.get("ir_pdfs") or {}
        mca    = d.get("mca_pdfs") or {}
        print(col.format(
            cid,
            str(prices.get("count", "-")),
            str(ir.get("uploaded", 0)),
            str(mca.get("uploaded", 0)),
        ))

    print()
    print("  [OK]     Success :", result.successful)
    print("  [FAIL]   Failed  :", result.failed)
    print("  [WARN]   Errors  :", len(result.errors))
    print("  [TIME]   Duration:", f"{result.duration_seconds:.1f}s")

    if result.errors:
        print()
        print("  Error details:")
        for e in result.errors:
            print(f"    [{e['company_id']}/{e['source']}] {e['error'][:90]}")

    print()
    print(sep)
    print("  S3 Layout under", bucket + "/")
    print("    {CO}/prices/          -> Yahoo OHLCV + financials JSON")
    print("    {CO}/Annual_Reports/  -> BSE + IR annual report PDFs")
    print("    {CO}/Quarterly_Results/ -> BSE quarterly result PDFs")
    print("    {CO}/MCA_Filings/     -> MCA AOC-4 / MGT-7 PDFs")
    print(sep)
    print()


if __name__ == "__main__":
    main()
