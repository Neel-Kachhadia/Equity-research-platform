"""
EREBUS · Alpha 06 — Credibility Alpha (α₆)
============================================
Formula (raw, pre-normalisation):
  CredibilityAlpha = 0.5 × GuidanceAcc
                   + 0.3 × SentimentTrend
                   − 0.2 × HedgeLanguageRatio

Where:
  GuidanceAcc       = guidance hits / total guidance points given
                      (management accuracy on forward statements)
  SentimentTrend    = trajectory of FinBERT sentiment score over periods
                      (e.g. current_score − rolling_avg)
  HedgeLanguageRatio= hedge/qualifier tokens / total tokens in earnings call
                      ("may", "could", "subject to", "approximately", etc.)

High guidance accuracy + improving sentiment + low hedging → high credibility
MCS (Management Credibility Score) is a derived concept built from these inputs.

Output is raw (unbounded). Caller normalises to [−100, +100].
"""

from __future__ import annotations
import statistics
from typing import Optional


# ── Hedge Language Detection ───────────────────────────────────────────────────
# Common hedge/qualifier tokens in financial earnings calls
HEDGE_TOKENS = {
    "may", "might", "could", "should", "would", "can",
    "approximately", "roughly", "around", "about", "nearly",
    "subject to", "depending on", "if", "assuming", "expect",
    "anticipate", "believe", "estimate", "project", "target",
    "guidance", "outlook", "forecast", "potentially", "possible",
    "uncertain", "fluctuate", "volatile", "challenging", "headwind",
    "difficult", "risk", "contingent", "conditional",
}


def compute_hedge_ratio(transcript_text: str) -> float:
    """
    Compute HedgeLanguageRatio from raw earnings call text.
    = hedge token matches / total words
    Returns a value in [0, 1].
    """
    if not transcript_text:
        return 0.3  # assume moderate hedging if no text
    words = transcript_text.lower().split()
    total = len(words)
    if total == 0:
        return 0.3
    hedge_count = sum(1 for w in words if w.strip(".,;:!?\"'()") in HEDGE_TOKENS)
    return min(1.0, hedge_count / total)


def compute_sentiment_trend(
    sentiment_scores: list[float],  # e.g. [0.6, 0.58, 0.61, 0.65] chronological
    lookback: int = 2,
) -> float:
    """
    SentimentTrend = current_score − rolling_average_over_lookback_periods.
    Returns a signed float: positive = improving, negative = deteriorating.
    """
    clean = [s for s in sentiment_scores if s is not None]
    if len(clean) < 2:
        return 0.0
    current = clean[-1]
    # Average of the prior `lookback` periods (not including current)
    prior = clean[-(lookback + 1):-1]
    if not prior:
        return 0.0
    prior_avg = statistics.mean(prior)
    return current - prior_avg


def compute_guidance_accuracy(
    promised_values: list[float],  # management guidance values
    actual_values: list[float],    # actual reported values
    tolerance: float = 0.05,       # ±5% counts as a hit
) -> Optional[float]:
    """
    GuidanceAcc = hits / total guidance points.
    A hit = |actual − guidance| / |guidance| ≤ tolerance.
    Returns None if no guidance data.
    """
    if not promised_values or not actual_values:
        return None
    pairs = [
        (p, a) for p, a in zip(promised_values, actual_values)
        if p is not None and a is not None and p != 0
    ]
    if not pairs:
        return None
    hits = sum(
        1 for p, a in pairs
        if abs(a - p) / abs(p) <= tolerance
    )
    return hits / len(pairs)


def compute_credibility_alpha(
    guidance_promised: list[float] = None,  # historical guidance values
    guidance_actual: list[float] = None,    # corresponding actual results
    sentiment_scores: list[float] = None,   # FinBERT-derived scores per period [0,1]
    transcript_text: str = None,            # latest earnings call transcript
    guidance_accuracy: float = None,        # pre-computed, overrides guidance_promised/actual
    hedge_ratio: float = None,              # pre-computed, overrides transcript_text
    sentiment_trend: float = None,          # pre-computed, overrides sentiment_scores
) -> dict:
    """
    Compute Credibility Alpha (α₆) — Management Credibility Score (MCS).

    Parameters
    ----------
    guidance_promised : list[float]
        Historical management guidance values (e.g. revenue targets).
    guidance_actual : list[float]
        Corresponding realised values.
    sentiment_scores : list[float]
        Chronological FinBERT sentiment scores (0=negative, 1=positive).
    transcript_text : str
        Latest earnings call transcript text for hedge language detection.
    *_precomputed   : float
        Optional pre-computed values (override raw inputs if provided).

    Returns
    -------
    dict with keys:
        raw_score         : float
        guidance_accuracy : float — [0,1]
        sentiment_trend   : float — signed trend
        hedge_ratio       : float — [0,1]
        data_flags        : list
    """
    data_flags = []

    # ── Guidance Accuracy ─────────────────────────────────────────────────────
    if guidance_accuracy is not None:
        g_acc = guidance_accuracy
    else:
        g_acc = compute_guidance_accuracy(guidance_promised, guidance_actual)
        if g_acc is None:
            g_acc = 0.5  # neutral: no guidance data
            data_flags.append("guidance_accuracy_imputed_neutral: no guidance data")

    # ── Sentiment Trend ───────────────────────────────────────────────────────
    if sentiment_trend is not None:
        s_trend = sentiment_trend
    else:
        scores = sentiment_scores or []
        s_trend = compute_sentiment_trend(scores)
        if not scores or len([s for s in scores if s is not None]) < 2:
            data_flags.append("sentiment_trend_imputed_zero: need ≥2 sentiment periods")

    # ── Hedge Language Ratio ──────────────────────────────────────────────────
    if hedge_ratio is not None:
        h_ratio = hedge_ratio
    else:
        h_ratio = compute_hedge_ratio(transcript_text or "")
        if not transcript_text:
            data_flags.append("hedge_ratio_imputed_moderate: no transcript provided")

    # ── Composite Raw Score ───────────────────────────────────────────────────
    raw_score = (
        0.5  *  g_acc +
        0.3  *  s_trend +
        -0.2 *  h_ratio
    )

    return {
        "alpha_id": "α₆",
        "alpha_name": "Credibility Alpha",
        "raw_score": raw_score,
        "guidance_accuracy": g_acc,
        "sentiment_trend": s_trend,
        "hedge_ratio": h_ratio,
        "data_flags": data_flags,
    }
