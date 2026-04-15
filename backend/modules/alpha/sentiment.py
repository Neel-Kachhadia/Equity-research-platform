"""
EREBUS · Alpha 07 — Sentiment Alpha (α₇)
==========================================
Formula (raw, pre-normalisation):
  SentimentAlpha = 0.5 × FinBERT_pos_ratio(t)
                 + 0.3 × Δ_sentiment(t, t−2)
                 − 0.2 × FinBERT_neg_ratio(t)

Where:
  FinBERT_pos_ratio(t) = positive sentences / total sentences  (current period)
  FinBERT_neg_ratio(t) = negative sentences / total sentences  (current period)
  Δ_sentiment(t, t−2) = current composite score − 2-year average score
                         (positive = improving, negative = deteriorating)

The FinBERT scores are derived from earnings call transcripts and MD&A sections.
In the context of EREBUS, these are pre-computed upstream (by the sentiment module)
and passed in as aggregated ratios.

Output is raw (unbounded). Caller normalises to [−100, +100].
"""

from __future__ import annotations
import statistics
from typing import Optional


def compute_delta_sentiment(
    sentiment_scores: list[float],  # chronological composite sentiment [0,1]
    lookback: int = 2,
) -> float:
    """
    Δ_sentiment = current_score − average score over last `lookback` periods.
    Positive = improving trend. Negative = deteriorating.
    """
    clean = [s for s in sentiment_scores if s is not None]
    if len(clean) < 2:
        return 0.0
    current = clean[-1]
    # Average of prior `lookback` values (not including current)
    prior = clean[-(lookback + 1):-1] if len(clean) > lookback else clean[:-1]
    if not prior:
        return 0.0
    return current - statistics.mean(prior)


def compute_sentiment_alpha(
    finbert_pos_ratio: float,            # positive sentences / total (latest period) [0,1]
    finbert_neg_ratio: float,            # negative sentences / total (latest period) [0,1]
    sentiment_score_series: list[float] = None,  # chronological scores for trend calc
    delta_sentiment: float = None,       # pre-computed delta (overrides series)
) -> dict:
    """
    Compute Sentiment Alpha (α₇).

    Parameters
    ----------
    finbert_pos_ratio : float
        Fraction of sentences classified as positive by FinBERT in latest period.
        Range [0, 1].
    finbert_neg_ratio : float
        Fraction of sentences classified as negative. Range [0, 1].
    sentiment_score_series : list[float]
        Chronological composite FinBERT sentiment scores per period [0,1].
        Used to compute the 2-year sentiment trend.
    delta_sentiment : float
        Pre-computed Δ_sentiment. If provided, overrides series calculation.

    Returns
    -------
    dict with keys:
        raw_score          : float
        finbert_pos_ratio  : float
        finbert_neg_ratio  : float
        delta_sentiment    : float
        data_flags         : list
    """
    data_flags = []

    # ── Validate / Default Ratios ─────────────────────────────────────────────
    if finbert_pos_ratio is None:
        finbert_pos_ratio = 0.5
        data_flags.append("pos_ratio_imputed_neutral: FinBERT output not provided")
    if finbert_neg_ratio is None:
        finbert_neg_ratio = 0.2
        data_flags.append("neg_ratio_imputed_neutral: FinBERT output not provided")

    # Clamp to [0, 1]
    finbert_pos_ratio = max(0.0, min(1.0, finbert_pos_ratio))
    finbert_neg_ratio = max(0.0, min(1.0, finbert_neg_ratio))

    # ── Δ Sentiment ───────────────────────────────────────────────────────────
    if delta_sentiment is not None:
        d_sentiment = delta_sentiment
    else:
        series = sentiment_score_series or []
        d_sentiment = compute_delta_sentiment(series, lookback=2)
        if len([s for s in series if s is not None]) < 3:
            data_flags.append("delta_sentiment_imputed_zero: need ≥3 sentiment periods for 2yr delta")

    # ── Composite Raw Score ───────────────────────────────────────────────────
    raw_score = (
        0.5  * finbert_pos_ratio +
        0.3  * d_sentiment +
        -0.2 * finbert_neg_ratio
    )

    return {
        "alpha_id": "α₇",
        "alpha_name": "Sentiment Alpha",
        "raw_score": raw_score,
        "finbert_pos_ratio": finbert_pos_ratio,
        "finbert_neg_ratio": finbert_neg_ratio,
        "delta_sentiment": d_sentiment,
        "data_flags": data_flags,
    }
