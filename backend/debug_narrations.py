"""
Debug: print the actual parsed narrations from the pnl sheet for Infosys and TCS.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('.env', override=True)
sys.path.insert(0, os.path.dirname(__file__))

from modules.ingestion.company_loader import (
    _get_s3_client, _fetch_bytes, _read_excel, _read_excel_wide_format, _BUCKET
)

for company, xl_key in [
    ("Infosys", "Infosys.xlsx"),
    ("TCS",     "TCS/Quarterly_Results/2026_TCS-Data-Sheet-Q3FY26.xlsx"),
    ("TCS root","TCS.xlsx"),
]:
    print(f"\n=== {company}: {xl_key} ===")
    try:
        raw = _fetch_bytes(xl_key)
        sheets = _read_excel(raw)
        if not any(v.get("rows") for v in sheets.values()):
            sheets = _read_excel_wide_format(raw)
            print("  (using wide format)")
        pnl = sheets.get("pnl", {})
        rows = pnl.get("rows", [])
        print(f"  pnl rows: {len(rows)}")
        # Print first 15 narrations with first non-None value
        for r in rows[:15]:
            narr = r["narration"]
            vals = [v for v in r["values"] if v is not None]
            first_val = vals[-1] if vals else None
            print(f"    '{narr}' => last_val={first_val}")
    except Exception as e:
        print(f"  ERROR: {e}")
