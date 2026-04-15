import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from modules.quant.ratios import compute_revenue_growth, compute_single_period_ratios
from modules.quant.trends import compute_trend_slope
from modules.quant.volatility import compute_parkinson_estimator
from modules.quant.risk import compute_absolute_risk_score

def test_quant():
    rev_growth = compute_revenue_growth([100, 110, 120, 130])
    print("Rev growth:", rev_growth)
    
    ratios = compute_single_period_ratios(revenue=1000, pat=150, equity=500, total_debt=250, fcf=120, ebit=200, interest_expense=20)
    print("Ratios:", ratios)
    
    trend = compute_trend_slope([0.15, 0.16, 0.18, 0.14, 0.12])
    print("Trend:", trend)
    
    parkinson = compute_parkinson_estimator([120, 125, 130], [100, 110, 105])
    print("Parkinson:", parkinson)
    
    risk = compute_absolute_risk_score(
        debt_to_equity=0.5,
        fcf_conversion=0.8,
        margin_trend_slope=-0.015,
        volatility=0.05,
        sentiment_flag=False
    )
    print("Risk:", risk)

if __name__ == "__main__":
    test_quant()
