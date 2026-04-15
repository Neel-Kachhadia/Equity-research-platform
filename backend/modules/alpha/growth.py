"""
EREBUS · Alpha 01 — Growth Alpha (α₁)
======================================
Formula (raw, pre-normalisation):
  GrowthAlpha = 0.5 × CAGR_rev(5yr)
              + 0.3 × CAGR_ebit(5yr)
              + 0.2 × Δrev_vs_sector_median

Where:
  CAGR = (V_n / V_0)^(1/n) − 1
  Δrev_vs_sector = company CAGR − peer median CAGR

Output is raw (unbounded), caller normalises to [−100, +100] via percentile rank.
"""

from __future__ import annotations
import math
from typing import Optional


def compute_cagr(values: list[float]) -> Optional[float]:
    """
    Compute CAGR from a time-ordered list of values.
    CAGR = (V_n / V_0)^(1/n) - 1
    Returns None if data is insufficient or invalid.
    """
    # Filter out zeroes / None
    clean = [v for v in values if v is not None and v != 0]
    if len(clean) < 2:
        return None
    v0, vn = clean[0], clean[-1]
    n = len(clean) - 1
    if v0 <= 0 or vn <= 0:
        return None
    return (vn / v0) ** (1.0 / n) - 1.0


def compute_growth_alpha(
    revenue_series: list[float],          # 5 years of revenue, chronological order
    ebit_series: list[float],             # 5 years of EBIT, chronological order
    sector_peer_revenue_cagrs: list[float],  # CAGR values for sector peers
) -> dict:
    """
    Compute Growth Alpha (α₁).

    Parameters
    ----------
    revenue_series : list[float]
        Chronological annual revenue figures (ideally 5–6 values for 5yr CAGR).
    ebit_series : list[float]
        Chronological annual EBIT figures.
    sector_peer_revenue_cagrs : list[float]
        Revenue CAGRs of sector peers (used to compute Δrev_vs_sector_median).

    Returns
    -------
    dict with keys:
        raw_score       : float  — unbounded raw alpha score
        cagr_rev        : float  — 5yr revenue CAGR
        cagr_ebit       : float  — 5yr EBIT CAGR
        delta_vs_sector : float  — company CAGR − peer median CAGR
        data_flags      : list   — any missing / imputed data warnings
    """
    data_flags = []

    # ── Revenue CAGR ──────────────────────────────────────────────────────────
    cagr_rev = compute_cagr(revenue_series)
    if cagr_rev is None:
        cagr_rev = 0.0
        data_flags.append("revenue_cagr_imputed_zero: insufficient data")

    # ── EBIT CAGR ─────────────────────────────────────────────────────────────
    cagr_ebit = compute_cagr(ebit_series)
    if cagr_ebit is None:
        cagr_ebit = 0.0
        data_flags.append("ebit_cagr_imputed_zero: insufficient data")

    # ── Δ vs Sector Median ────────────────────────────────────────────────────
    if sector_peer_revenue_cagrs:
        valid_peers = [c for c in sector_peer_revenue_cagrs if c is not None]
        if valid_peers:
            sector_median = _median(valid_peers)
            delta_vs_sector = cagr_rev - sector_median
        else:
            delta_vs_sector = 0.0
            data_flags.append("sector_median_imputed_zero: no valid peer CAGRs")
    else:
        delta_vs_sector = 0.0
        data_flags.append("sector_median_imputed_zero: no peer data provided")

    # ── Composite Raw Score ───────────────────────────────────────────────────
    raw_score = (
        0.5 * cagr_rev +
        0.3 * cagr_ebit +
        0.2 * delta_vs_sector
    )

    return {
        "alpha_id": "α₁",
        "alpha_name": "Growth Alpha",
        "raw_score": raw_score,
        "cagr_rev": cagr_rev,
        "cagr_ebit": cagr_ebit,
        "delta_vs_sector": delta_vs_sector,
        "data_flags": data_flags,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 != 0 else (s[mid - 1] + s[mid]) / 2.0
