"""
EREBUS · Alpha 08 — Relative Strength Alpha (α₈)
==================================================
Formula (raw, pre-normalisation):
  RelStrengthAlpha = 0.40 × PctRank_rev_growth
                   + 0.35 × PctRank_NPM
                   + 0.25 × PctRank_ROE

Where:
  PctRank_X = percentile rank of company's X within its sector universe
  Scaled:    rank_pct × 2 − 1  →  maps [0, 1] percentile to [−1, +1]

All three PctRanks are scaled to [−1, +1] before weighting.
OutputMapping: top decile company → RelStrengthAlpha ≈ +1 (pre-normalisation)

This alpha identifies outperformers and laggards within peer groups.
Feeds the cross-sectional ranking model (M09).

Output is raw (approximately [−1, +1]). Caller normalises to [−100, +100].
"""

from __future__ import annotations
from typing import Optional


def compute_percentile_rank(value: float, universe: list[float]) -> Optional[float]:
    """
    Compute percentile rank of `value` within `universe`.
    Returns a float in [0, 1].
    - 0.0 = worst in universe
    - 1.0 = best in universe

    Uses: rank = (number of values strictly less than value) / (n - 1)
    """
    valid = [v for v in universe if v is not None]
    if not valid:
        return None
    n = len(valid)
    if n == 1:
        return 0.5  # only company; assign neutral
    rank = sum(1 for v in valid if v < value) / (n - 1)
    return max(0.0, min(1.0, rank))


def _scale_pct_rank(pct: float) -> float:
    """Scale percentile rank from [0,1] → [−1, +1] as per architecture spec."""
    return pct * 2.0 - 1.0


def compute_relative_strength_alpha(
    company_rev_growth: float,             # company's 5yr revenue CAGR
    company_npm: float,                    # company's latest net profit margin
    company_roe: float,                    # company's latest ROE
    sector_rev_growths: list[float],       # peer universe revenue CAGRs
    sector_npms: list[float],             # peer universe NPM values
    sector_roes: list[float],             # peer universe ROE values
) -> dict:
    """
    Compute Relative Strength Alpha (α₈).

    Parameters
    ----------
    company_rev_growth : float
        Company's revenue CAGR (e.g. 0.12 = 12% CAGR).
    company_npm : float
        Company's net profit margin (decimal).
    company_roe : float
        Company's Return on Equity (decimal).
    sector_rev_growths : list[float]
        All peers' revenue CAGRs (including the company itself).
    sector_npms : list[float]
        All peers' NPM values.
    sector_roes : list[float]
        All peers' ROE values.

    Returns
    -------
    dict with keys:
        raw_score        : float — approximately [−1, +1]
        pct_rank_rev     : float — percentile rank [0,1]
        pct_rank_npm     : float — percentile rank [0,1]
        pct_rank_roe     : float — percentile rank [0,1]
        scaled_rank_rev  : float — scaled to [−1, +1]
        scaled_rank_npm  : float
        scaled_rank_roe  : float
        data_flags       : list
    """
    data_flags = []

    # ── Revenue Growth Rank ───────────────────────────────────────────────────
    if company_rev_growth is not None and sector_rev_growths:
        pct_rev = compute_percentile_rank(company_rev_growth, sector_rev_growths)
    else:
        pct_rev = None
    if pct_rev is None:
        pct_rev = 0.5
        data_flags.append("rev_growth_rank_imputed_neutral: no peer data or missing value")
    scaled_rev = _scale_pct_rank(pct_rev)

    # ── NPM Rank ──────────────────────────────────────────────────────────────
    if company_npm is not None and sector_npms:
        pct_npm = compute_percentile_rank(company_npm, sector_npms)
    else:
        pct_npm = None
    if pct_npm is None:
        pct_npm = 0.5
        data_flags.append("npm_rank_imputed_neutral: no peer data or missing value")
    scaled_npm = _scale_pct_rank(pct_npm)

    # ── ROE Rank ──────────────────────────────────────────────────────────────
    if company_roe is not None and sector_roes:
        pct_roe = compute_percentile_rank(company_roe, sector_roes)
    else:
        pct_roe = None
    if pct_roe is None:
        pct_roe = 0.5
        data_flags.append("roe_rank_imputed_neutral: no peer data or missing value")
    scaled_roe = _scale_pct_rank(pct_roe)

    # ── Composite Raw Score ───────────────────────────────────────────────────
    raw_score = (
        0.40 * scaled_rev +
        0.35 * scaled_npm +
        0.25 * scaled_roe
    )

    return {
        "alpha_id": "α₈",
        "alpha_name": "Relative Strength Alpha",
        "raw_score": raw_score,
        "pct_rank_rev": pct_rev,
        "pct_rank_npm": pct_npm,
        "pct_rank_roe": pct_roe,
        "scaled_rank_rev": scaled_rev,
        "scaled_rank_npm": scaled_npm,
        "scaled_rank_roe": scaled_roe,
        "data_flags": data_flags,
    }
