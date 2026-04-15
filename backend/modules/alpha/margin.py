"""
EREBUS · Alpha 02 — Margin Alpha (α₂)
======================================
Formula (raw, pre-normalisation):
  MarginAlpha = 0.40 × Δ_NPM(t, t−3)
              + 0.35 × Δ_EBIT_margin(t, t−3)
              + 0.25 × Δ_gross_margin(t, t−3)

Where:
  Δ_M = M_t − M_{t-3}   (percentage-point change over 3 years)
  Positive = expanding margin structure (bullish)
  Negative = compressing margin structure (bearish)

All margin inputs expected as decimals (e.g. 0.15 = 15%).
Output is raw (unbounded). Caller normalises to [−100, +100].
"""

from __future__ import annotations
from typing import Optional


def compute_margin_delta(series: list[float], lookback: int = 3) -> Optional[float]:
    """
    Compute Δ_margin = M_t − M_{t-lookback}.
    Expects chronologically ordered series. Returns None if insufficient data.
    """
    clean = [v for v in series if v is not None]
    if len(clean) < lookback + 1:
        return None
    return clean[-1] - clean[-(lookback + 1)]


def compute_margin_alpha(
    npm_series: list[float],          # Net Profit Margin series (decimal), chronological
    ebit_margin_series: list[float],  # EBIT Margin series (decimal), chronological
    gross_margin_series: list[float], # Gross Margin series (decimal), chronological
    lookback: int = 3,                # years for delta computation (default 3)
) -> dict:
    """
    Compute Margin Alpha (α₂).

    Parameters
    ----------
    npm_series : list[float]
        Annual Net Profit Margin values as decimals (e.g. [0.12, 0.13, 0.14, 0.15]).
    ebit_margin_series : list[float]
        Annual EBIT Margin values as decimals.
    gross_margin_series : list[float]
        Annual Gross Margin values as decimals.
    lookback : int
        Number of years to compute the delta over (default 3 as per architecture).

    Returns
    -------
    dict with keys:
        raw_score        : float — unbounded raw alpha score
        delta_npm        : float — change in NPM over lookback period (pp)
        delta_ebit_margin: float — change in EBIT margin over lookback period
        delta_gross_margin: float — change in gross margin over lookback period
        data_flags       : list  — missing / imputed data warnings
    """
    data_flags = []

    # ── Δ Net Profit Margin ───────────────────────────────────────────────────
    delta_npm = compute_margin_delta(npm_series, lookback)
    if delta_npm is None:
        delta_npm = 0.0
        data_flags.append(f"delta_npm_imputed_zero: need ≥{lookback+1} years of NPM data")

    # ── Δ EBIT Margin ─────────────────────────────────────────────────────────
    delta_ebit = compute_margin_delta(ebit_margin_series, lookback)
    if delta_ebit is None:
        delta_ebit = 0.0
        data_flags.append(f"delta_ebit_margin_imputed_zero: need ≥{lookback+1} years of EBIT margin data")

    # ── Δ Gross Margin ────────────────────────────────────────────────────────
    delta_gross = compute_margin_delta(gross_margin_series, lookback)
    if delta_gross is None:
        delta_gross = 0.0
        data_flags.append(f"delta_gross_margin_imputed_zero: need ≥{lookback+1} years of gross margin data")

    # ── Composite Raw Score ───────────────────────────────────────────────────
    # Convert pp change (decimal) to percentage points for intuitive scoring
    # e.g. Δ_NPM = 0.03 means +3pp improvement → large positive signal
    raw_score = (
        0.40 * delta_npm +
        0.35 * delta_ebit +
        0.25 * delta_gross
    )

    return {
        "alpha_id": "α₂",
        "alpha_name": "Margin Alpha",
        "raw_score": raw_score,
        "delta_npm": delta_npm,
        "delta_ebit_margin": delta_ebit,
        "delta_gross_margin": delta_gross,
        "lookback_years": lookback,
        "data_flags": data_flags,
    }
