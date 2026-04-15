"""
EREBUS · Alpha 05 — Volatility Alpha (α₅)
===========================================
Formula (raw, pre-normalisation):
  VolatilityAlpha = −0.5 × σ_rev_growth(3yr)
                  − 0.3 × Parkinson_vol
                  − 0.2 × σ_ebit_margin(3yr)

Where:
  σ_rev_growth    = std dev of annual revenue growth rates over 3 years
  Parkinson_vol   = √( 1/(4n·ln2) × Σ ln(H_i / L_i)² )
                    H_i = high metric value, L_i = low metric value in period i
  σ_ebit_margin   = std dev of EBIT margin over 3 years

All terms are negative contributors: higher volatility → more negative alpha.
Stable businesses score positively; erratic/cyclical ones score negatively.

Output is raw (unbounded). Caller normalises to [−100, +100].
"""

from __future__ import annotations
import math
import statistics
from typing import Optional


def compute_sigma_growth(series: list[float], lookback: int = 3) -> Optional[float]:
    """
    Standard deviation of YoY growth rates over the last `lookback` years.
    Returns None if insufficient data.
    """
    clean = [v for v in series if v is not None]
    if len(clean) < lookback + 1:
        return None
    # Use last (lookback+1) values to get `lookback` YoY rates
    tail = clean[-(lookback + 1):]
    yoy_rates = []
    for i in range(1, len(tail)):
        if tail[i - 1] != 0:
            yoy_rates.append((tail[i] - tail[i - 1]) / abs(tail[i - 1]))
    if len(yoy_rates) < 2:
        return None
    return statistics.stdev(yoy_rates)


def compute_parkinson_volatility(
    high_values: list[float],
    low_values: list[float],
) -> Optional[float]:
    """
    Parkinson Volatility Estimator:
      σ_P = √( 1/(4n·ln2) × Σ_i ln(H_i / L_i)² )

    Uses the high-low range of a metric across reporting periods.
    More efficient than standard deviation for small samples.

    Parameters
    ----------
    high_values : list[float]
        The high (peak) value of the metric in each period.
    low_values  : list[float]
        The low (trough) value of the same metric in each period.
    """
    if not high_values or not low_values:
        return None
    if len(high_values) != len(low_values):
        return None

    valid_pairs = [
        (h, l) for h, l in zip(high_values, low_values)
        if h is not None and l is not None and l > 0 and h >= l
    ]
    if not valid_pairs:
        return None

    n = len(valid_pairs)
    log2 = math.log(2)
    sum_sq = sum(math.log(h / l) ** 2 for h, l in valid_pairs)
    parkinson = math.sqrt(sum_sq / (4 * n * log2))
    return parkinson


def compute_sigma_margin(series: list[float], lookback: int = 3) -> Optional[float]:
    """Standard deviation of EBIT margin over last `lookback` periods."""
    clean = [v for v in series if v is not None]
    tail = clean[-lookback:] if len(clean) >= lookback else clean
    if len(tail) < 2:
        return None
    return statistics.stdev(tail)


def compute_volatility_alpha(
    revenue_series: list[float],          # chronological annual revenue (≥4 values for 3yr σ)
    ebit_margin_series: list[float],      # chronological EBIT margin as decimal
    # Parkinson inputs: high/low of a key metric across periods (e.g. quarterly EBIT margin)
    metric_highs: list[float] = None,     # optional: high values per period
    metric_lows: list[float] = None,      # optional: low values per period
    lookback: int = 3,
) -> dict:
    """
    Compute Volatility Alpha (α₅).

    Parameters
    ----------
    revenue_series : list[float]
        Annual revenue, chronological. Used for σ_rev_growth.
    ebit_margin_series : list[float]
        Annual EBIT margin (decimal). Used for σ_ebit_margin.
    metric_highs, metric_lows : list[float]
        Period-level high/low of a key metric for Parkinson estimator.
        If not provided, Parkinson is estimated from EBIT margin range.
    lookback : int
        Rolling window in years (default 3).

    Returns
    -------
    dict with keys:
        raw_score       : float
        sigma_rev_growth: float
        parkinson_vol   : float
        sigma_ebit_margin: float
        data_flags      : list
    """
    data_flags = []

    # ── σ Revenue Growth ──────────────────────────────────────────────────────
    sigma_rev = compute_sigma_growth(revenue_series, lookback)
    if sigma_rev is None:
        sigma_rev = 0.10  # neutral-high default
        data_flags.append(f"sigma_rev_imputed: need ≥{lookback+1} years revenue data")

    # ── Parkinson Volatility ──────────────────────────────────────────────────
    if metric_highs and metric_lows:
        parkinson = compute_parkinson_volatility(metric_highs, metric_lows)
    else:
        # Estimate from EBIT margin: use annual values as single-period "ranges"
        # Parkinson from rolling max/min within the series as surrogate
        clean_margins = [v for v in ebit_margin_series if v is not None]
        if len(clean_margins) >= 2:
            # Create synthetic high/low pairs from consecutive periods
            highs = [max(clean_margins[i], clean_margins[i+1]) for i in range(len(clean_margins)-1)]
            lows  = [min(clean_margins[i], clean_margins[i+1]) for i in range(len(clean_margins)-1)]
            # Avoid log(h/l) where h==l → substitute tiny epsilon
            lows  = [l if l > 0 else 1e-6 for l in lows]
            highs = [h if h > 0 else l * 1.0001 for h, l in zip(highs, lows)]
            parkinson = compute_parkinson_volatility(highs, lows)
        else:
            parkinson = None
        if parkinson is None:
            data_flags.append("parkinson_imputed_zero: no metric high/low data")
            parkinson = 0.0

    # ── σ EBIT Margin ─────────────────────────────────────────────────────────
    sigma_ebit = compute_sigma_margin(ebit_margin_series, lookback)
    if sigma_ebit is None:
        sigma_ebit = 0.05  # neutral
        data_flags.append(f"sigma_ebit_margin_imputed: need ≥2 EBIT margin values")

    # ── Composite Raw Score ───────────────────────────────────────────────────
    # All terms are negative: higher volatility → worse score
    raw_score = (
        -0.5 * sigma_rev +
        -0.3 * parkinson +
        -0.2 * sigma_ebit
    )

    return {
        "alpha_id": "α₅",
        "alpha_name": "Volatility Alpha",
        "raw_score": raw_score,
        "sigma_rev_growth": sigma_rev,
        "parkinson_vol": parkinson,
        "sigma_ebit_margin": sigma_ebit,
        "data_flags": data_flags,
    }
