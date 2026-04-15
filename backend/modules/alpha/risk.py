"""
EREBUS · Alpha 04 — Risk Alpha (α₄)
=====================================
Formula (raw, pre-normalisation):
  RiskAlpha = −0.30 × norm(D/E)
            − 0.25 × norm(1 / ICR)
            − 0.25 × norm(σ_margin)
            + 0.20 × norm(FCF_conv)

Where:
  D/E       = Total Debt / Shareholders' Equity (leverage)
  ICR       = EBIT / Interest Expense (interest coverage ratio)
  σ_margin  = standard deviation of net profit margin over 3 years
  FCF_conv  = FCF / Net Income (free cash flow conversion)
  norm(x)   = (x − x_min) / (x_max − x_min) → [0, 1]
              using cross-sectional peer universe bounds

High leverage, low coverage, volatile margins → negative alpha (risky)
Strong FCF conversion → positive contribution

Output is raw (unbounded). Caller normalises to [−100, +100].
"""

from __future__ import annotations
import math
import statistics
from typing import Optional


def _min_max_norm(value: float, min_val: float, max_val: float) -> float:
    """
    Min-max normalise to [0, 1].
    If range is zero, return 0.5 (neutral).
    """
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compute_sigma_margin(npm_series: list[float]) -> Optional[float]:
    """Standard deviation of net profit margin over available years."""
    clean = [v for v in npm_series if v is not None]
    if len(clean) < 2:
        return None
    return statistics.stdev(clean)


def compute_risk_alpha(
    debt_to_equity: float,             # D/E ratio (current year)
    interest_coverage_ratio: float,    # EBIT / Interest Expense (current year)
    npm_series: list[float],           # Net profit margin series (≥3 years)
    fcf_conversion: float,             # FCF / Net Income (current year)
    # Peer universe bounds for normalisation (if None, raw values used)
    de_bounds: tuple[float, float] = (0.0, 5.0),
    icr_bounds: tuple[float, float] = (0.5, 20.0),
    sigma_margin_bounds: tuple[float, float] = (0.0, 0.15),
    fcf_conv_bounds: tuple[float, float] = (0.0, 2.0),
) -> dict:
    """
    Compute Risk Alpha (α₄).

    Parameters
    ----------
    debt_to_equity : float
        D/E ratio. Higher = more leveraged = negative signal.
    interest_coverage_ratio : float
        ICR = EBIT / Interest Expense. We use 1/ICR so higher ICR → lower risk.
    npm_series : list[float]
        Net profit margin (decimal) over ≥3 years for σ computation.
    fcf_conversion : float
        FCF / Net Income. Higher = better cash quality = positive signal.
    *_bounds : tuple[float, float]
        (min, max) for peer-universe min-max normalisation.
        Defaults are calibrated for general Indian listed companies.

    Returns
    -------
    dict with keys:
        raw_score          : float
        norm_de            : float — normalised D/E [0,1]
        norm_inv_icr       : float — normalised 1/ICR [0,1]
        norm_sigma_margin  : float — normalised margin volatility [0,1]
        norm_fcf_conv      : float — normalised FCF conversion [0,1]
        data_flags         : list
    """
    data_flags = []

    # ── Normalise D/E ─────────────────────────────────────────────────────────
    de_val = max(0.0, debt_to_equity) if debt_to_equity is not None else None
    if de_val is None:
        de_val = 1.0  # neutral
        data_flags.append("de_imputed_neutral: D/E not provided")
    norm_de = _min_max_norm(de_val, *de_bounds)

    # ── Normalise 1/ICR ───────────────────────────────────────────────────────
    if interest_coverage_ratio is not None and interest_coverage_ratio != 0:
        inv_icr = 1.0 / max(0.1, interest_coverage_ratio)  # cap at 0.1 floor
    else:
        inv_icr = 1.0  # high risk (ICR = 0 or unknown)
        data_flags.append("inv_icr_imputed_high_risk: ICR zero or missing")
    # Invert bounds for normalisation: high 1/ICR = bad → high norm
    inv_icr_bounds = (1.0 / icr_bounds[1], 1.0 / icr_bounds[0])
    norm_inv_icr = _min_max_norm(inv_icr, *inv_icr_bounds)

    # ── σ of Margin ───────────────────────────────────────────────────────────
    sigma_margin = compute_sigma_margin(npm_series)
    if sigma_margin is None:
        sigma_margin = 0.05  # neutral
        data_flags.append("sigma_margin_imputed_neutral: need ≥2 years of NPM data")
    norm_sigma = _min_max_norm(sigma_margin, *sigma_margin_bounds)

    # ── FCF Conversion ────────────────────────────────────────────────────────
    fcf_val = fcf_conversion if fcf_conversion is not None else 0.5
    if fcf_conversion is None:
        data_flags.append("fcf_conv_imputed_neutral")
    norm_fcf = _min_max_norm(fcf_val, *fcf_conv_bounds)

    # ── Composite Raw Score ───────────────────────────────────────────────────
    # Risk factors are negative contributors; FCF is positive
    raw_score = (
        -0.30 * norm_de +
        -0.25 * norm_inv_icr +
        -0.25 * norm_sigma +
         0.20 * norm_fcf
    )

    return {
        "alpha_id": "α₄",
        "alpha_name": "Risk Alpha",
        "raw_score": raw_score,
        "norm_de": norm_de,
        "norm_inv_icr": norm_inv_icr,
        "norm_sigma_margin": norm_sigma,
        "norm_fcf_conv": norm_fcf,
        "sigma_margin_raw": sigma_margin,
        "data_flags": data_flags,
    }
