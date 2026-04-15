"""
EREBUS · Alpha 03 — Consistency Alpha (α₃)
============================================
Formula (raw, pre-normalisation):
  ConsistencyAlpha = −CV_rev  × 0.5
                   − CV_ebit × 0.3
                   + HitRate × 0.2

Where:
  CV  = σ / |μ|   (Coefficient of Variation)
  HitRate = years of YoY positive growth / total years observed

Lower CV  → more consistent → higher alpha (negative of CV is positive)
Higher HitRate → more years of growth → higher alpha

Output is raw (unbounded). Caller normalises to [−100, +100].
"""

from __future__ import annotations
import math
import statistics
from typing import Optional


def compute_cv(series: list[float]) -> Optional[float]:
    """
    Coefficient of Variation = σ / |μ|.
    Returns None if mean is zero or insufficient data.
    """
    clean = [v for v in series if v is not None]
    if len(clean) < 2:
        return None
    mean = statistics.mean(clean)
    if mean == 0:
        return None
    stdev = statistics.stdev(clean)
    return stdev / abs(mean)


def compute_hit_rate(series: list[float]) -> Optional[float]:
    """
    HitRate = fraction of years where YoY growth > 0.
    Requires at least 2 chronological values to compute YoY changes.
    """
    clean = [v for v in series if v is not None]
    if len(clean) < 2:
        return None
    yoy_changes = [clean[i] - clean[i - 1] for i in range(1, len(clean))]
    positive_years = sum(1 for c in yoy_changes if c > 0)
    return positive_years / len(yoy_changes)


def compute_consistency_alpha(
    revenue_series: list[float],  # chronological annual revenue
    ebit_series: list[float],     # chronological annual EBIT
) -> dict:
    """
    Compute Consistency Alpha (α₃).

    Parameters
    ----------
    revenue_series : list[float]
        Chronological annual revenue values (ideally 5+ years).
    ebit_series : list[float]
        Chronological annual EBIT values.

    Returns
    -------
    dict with keys:
        raw_score   : float — unbounded raw alpha score
        cv_rev      : float — coefficient of variation for revenue growth
        cv_ebit     : float — coefficient of variation for EBIT
        hit_rate    : float — fraction of years with positive YoY growth
        data_flags  : list
    """
    data_flags = []

    # ── Revenue YoY growth series for CV and HitRate ──────────────────────────
    rev_clean = [v for v in revenue_series if v is not None]
    rev_yoy = []
    if len(rev_clean) >= 2:
        for i in range(1, len(rev_clean)):
            if rev_clean[i - 1] != 0:
                rev_yoy.append((rev_clean[i] - rev_clean[i - 1]) / abs(rev_clean[i - 1]))
            else:
                rev_yoy.append(0.0)
    else:
        data_flags.append("revenue_yoy_insufficient: need ≥2 years of revenue data")

    # ── CV Revenue ────────────────────────────────────────────────────────────
    cv_rev = compute_cv(rev_yoy) if rev_yoy else None
    if cv_rev is None:
        cv_rev = 0.0
        data_flags.append("cv_rev_imputed_zero: insufficient or zero-mean revenue data")

    # ── CV EBIT ───────────────────────────────────────────────────────────────
    ebit_clean = [v for v in ebit_series if v is not None]
    ebit_yoy = []
    if len(ebit_clean) >= 2:
        for i in range(1, len(ebit_clean)):
            if ebit_clean[i - 1] != 0:
                ebit_yoy.append((ebit_clean[i] - ebit_clean[i - 1]) / abs(ebit_clean[i - 1]))
            else:
                ebit_yoy.append(0.0)
    cv_ebit = compute_cv(ebit_yoy) if ebit_yoy else None
    if cv_ebit is None:
        cv_ebit = 0.0
        data_flags.append("cv_ebit_imputed_zero: insufficient or zero-mean EBIT data")

    # ── HitRate (use revenue YoY) ─────────────────────────────────────────────
    hit_rate = compute_hit_rate(rev_clean) if len(rev_clean) >= 2 else None
    if hit_rate is None:
        hit_rate = 0.5
        data_flags.append("hit_rate_imputed_neutral: insufficient revenue data")

    # ── Composite Raw Score ───────────────────────────────────────────────────
    # Both CV terms are *negative* — lower CV = better consistency = positive alpha
    raw_score = (
        -cv_rev  * 0.5 +
        -cv_ebit * 0.3 +
         hit_rate * 0.2
    )

    return {
        "alpha_id": "α₃",
        "alpha_name": "Consistency Alpha",
        "raw_score": raw_score,
        "cv_rev": cv_rev,
        "cv_ebit": cv_ebit,
        "hit_rate": hit_rate,
        "data_flags": data_flags,
    }
