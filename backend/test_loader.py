"""
Quick end-to-end load test for all known companies in the bucket.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('.env', override=True)
sys.path.insert(0, os.path.dirname(__file__))

from modules.ingestion.company_loader import load_company, CompanyDataError

COMPANIES = ["TCS", "Infosys", "Wipro", "HCL_Tech", "Tech_Mahindra",
             "Mindtree", "Persistent", "Coforge"]

print("=" * 60)
print("Company Loader End-to-End Test")
print("=" * 60)

for company in COMPANIES:
    print(f"\n--- {company} ---")
    try:
        ctx = load_company(company)
        fin = ctx["financials"]
        stub = " [STUB - no Excel]" if fin.get("_stub") else ""
        print(f"  OK  Revenue:    {fin.get('revenue', 0):>12,.1f} Cr{stub}")
        print(f"  OK  Net Income: {fin.get('net_income', 0):>12,.1f} Cr")
        print(f"  OK  Prices:     {len(ctx['prices'])} data points")
        print(f"  OK  Text:       {'YES' if ctx.get('text') else 'no'} ({len(ctx.get('text','') or '')} chars)")
        print(f"  OK  Excel:      {ctx.get('raw_excel', {})}")
        print(f"  OK  Docs:       {len(ctx.get('documents', []))} indexed")
    except CompanyDataError as e:
        print(f"  FAIL CompanyDataError: {e}")
    except Exception as e:
        print(f"  FAIL {type(e).__name__}: {e}")

print("\n" + "=" * 60)
