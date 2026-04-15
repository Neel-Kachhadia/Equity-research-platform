"""
EREBUS · Alpha Module — Package Init
======================================
Public API for the alpha signal engine.

Quick-start example:
    from modules.alpha import AlphaInput, run_all_alphas

    result = run_all_alphas(AlphaInput(
        company_id="TCS",
        company_name="Tata Consultancy Services",
        sector="it",
        revenue_series=[1500, 1650, 1820, 2000, 2200],   # ₹ crore, FY20–FY24
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

    print(result["composite"]["summary"])
"""

from .signals import AlphaInput, run_all_alphas, normalise_raw_to_universe, normalise_raw_sigmoid
from .composite import compute_cas, compute_dci, compute_qsd, build_composite_output
from .growth import compute_growth_alpha
from .margin import compute_margin_alpha
from .consistency import compute_consistency_alpha
from .risk import compute_risk_alpha
from .volatility import compute_volatility_alpha
from .credibility import compute_credibility_alpha
from .sentiment import compute_sentiment_alpha
from .relative_strength import compute_relative_strength_alpha

__all__ = [
    # Unified entry point
    "AlphaInput",
    "run_all_alphas",

    # Normalisation utilities
    "normalise_raw_to_universe",
    "normalise_raw_sigmoid",

    # Composite signals
    "compute_cas",
    "compute_dci",
    "compute_qsd",
    "build_composite_output",

    # Individual alpha functions (for direct use)
    "compute_growth_alpha",
    "compute_margin_alpha",
    "compute_consistency_alpha",
    "compute_risk_alpha",
    "compute_volatility_alpha",
    "compute_credibility_alpha",
    "compute_sentiment_alpha",
    "compute_relative_strength_alpha",
]
