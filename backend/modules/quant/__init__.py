"""
Module: Quant Engine
====================
Entry point for all quantitative financial analysis.

Usage:
    from modules.quant import compute_quant_profile

    result = compute_quant_profile(
        prices=[101.2, 103.5, 99.8, ...],
        financials={"market_cap": 2e12, "net_income": 180e9, ...}
    )

Returns:
    {
        "ratios":     { ... },
        "trends":     { ... },
        "volatility": { ... },
        "risk":       { ... }
    }

Dependency order (enforced by compute_quant_profile):
    1. ratios     ← financials only
    2. trends     ← prices only
    3. volatility ← prices only
    4. risk       ← outputs of (1, 2, 3) — NOT raw inputs
"""

from typing import List, Dict, Any, Optional

from .ratios     import compute_all_ratios
from .trends     import compute_all_trends
from .volatility import compute_all_volatility
from .risk       import compute_all_risk

__version__ = "0.1.0"

__all__ = [
    "compute_quant_profile",
    "compute_all_ratios",
    "compute_all_trends",
    "compute_all_volatility",
    "compute_all_risk",
]


def compute_quant_profile(
    prices: List[float],
    financials: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Single entry point — compute full quantitative profile.

    Enforces strict dependency order:
        ratios and trends/volatility are computed independently,
        risk is always computed LAST from the other outputs.

    Args:
        prices:     List of close prices, chronological (oldest → newest).
        financials: Dict of financial statement data. Optional.
                    If None, ratio-dependent risk scoring is skipped.

    Returns:
        {
            "ratios":     dict | None
            "trends":     dict | None
            "volatility": dict | None
            "risk":       dict        (always returned, values may be None)
        }
    """
    # Step 1: Independent computations (no cross-dependency)
    ratios     = compute_all_ratios(financials)
    trends     = compute_all_trends(prices)
    volatility = compute_all_volatility(prices)

    # Step 2: Risk takes OUTPUTS of steps above — never raw inputs
    risk = compute_all_risk(
        ratios=ratios,
        trends=trends,
        volatility=volatility,
    )

    return {
        "ratios":     ratios,
        "trends":     trends,
        "volatility": volatility,
        "risk":       risk,
    }