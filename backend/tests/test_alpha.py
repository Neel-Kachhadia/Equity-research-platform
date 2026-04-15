import sys, json
sys.path.insert(0, 'backend')
from modules.alpha import AlphaInput, run_all_alphas

result = run_all_alphas(AlphaInput(
    company_id='TCS',
    company_name='Tata Consultancy Services',
    sector='it',
    revenue_series=[1500, 1650, 1820, 2000, 2200],
    ebit_series=[300, 330, 370, 405, 450],
    npm_series=[0.19, 0.20, 0.20, 0.21, 0.22],
    ebit_margin_series=[0.24, 0.25, 0.255, 0.26, 0.265],
    gross_margin_series=[0.35, 0.355, 0.36, 0.365, 0.37],
    debt_to_equity=0.05,
    interest_coverage_ratio=42.0,
    fcf_conversion=0.95,
    roe=0.38,
    available_fields=18,
    required_fields=20,
    years_available=5,
))

print("=== RAW ALPHAS ===")
print(json.dumps(result['raw_alphas'], indent=2))

print("\n=== NORMALISED ALPHAS ===")
print(json.dumps(result['normalised_alphas'], indent=2))

print("\n=== COMPOSITE SUMMARY ===")
print(json.dumps(result['composite']['summary'], indent=2))

print("\n=== DCI ===")
print(json.dumps(result['composite']['dci_result'], indent=2))

print("\n=== QSD ===")
print(json.dumps(result['composite']['qsd_result'], indent=2))

print("\n=== DATA FLAGS (non-empty only) ===")
for k, v in result['data_flags'].items():
    if v:
        print(f"  {k}: {v}")
