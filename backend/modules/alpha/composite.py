"""
EREBUS · Composite Alpha Score + Derived Signals
==================================================

Implements:
  1. CAS  — Composite Alpha Score
             CAS = 0.20·α₁ + 0.20·α₂ + 0.15·α₃ + 0.15·α₄ + 0.15·α₅
                 + 0.10·α₆ + 0.05·α₇ + 0.05·α₈
             Each αᵢ ∈ [−100, +100]  →  CAS ∈ [−100, +100]

  2. DCI  — Data Confidence Index
             DCI = 0.40·DataCoverage + 0.35·HistoryDepth + 0.25·AlphaAgreement
             DCI ∈ [0, 1]  displayed as 0–100%

  3. QSD  — Quant–Sentiment Divergence
             CAS_quant     = norm(α₁·0.28 + α₂·0.28 + α₃·0.20 + α₄·0.14 + α₅·0.10)
             CAS_sentiment = norm(α₆·0.60 + α₇·0.40)
             QSD = CAS_quant − CAS_sentiment  ∈ [−200, +200]
             |QSD| > 40 triggers divergence flag

Sector weight overrides (YAML-configurable):
  Default weights shown above.
  Banking/NBFC override: Growth→0.12, Risk→0.22, Credibility→0.18 (etc.)
"""

from __future__ import annotations
import math
import statistics
from typing import Optional


# ── Default CAS weights (from architecture §H) ────────────────────────────────
# NOTE: Architecture doc lists weights summing to 1.05 (typo).
# Fix: volatility reduced 0.15 → 0.10 (most correlated with Risk α₄).
DEFAULT_CAS_WEIGHTS = {
    "growth":       0.20,
    "margin":       0.20,
    "consistency":  0.15,
    "risk":         0.15,
    "volatility":   0.10,
    "credibility":  0.10,
    "sentiment":    0.05,
    "rel_strength": 0.05,
}

# ── Sector weight overrides ────────────────────────────────────────────────────
SECTOR_WEIGHT_OVERRIDES = {
    "banking": {
        "growth": 0.12,
        "margin": 0.12,
        "consistency": 0.12,
        "risk": 0.22,
        "volatility": 0.10,
        "credibility": 0.18,
        "sentiment": 0.07,
        "rel_strength": 0.07,
    },
    "nbfc": {
        "growth": 0.12,
        "margin": 0.12,
        "consistency": 0.12,
        "risk": 0.22,
        "volatility": 0.10,
        "credibility": 0.18,
        "sentiment": 0.07,
        "rel_strength": 0.07,
    },
}

# QSD divergence threshold
QSD_DIVERGENCE_THRESHOLD = 40.0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = -100.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _get_weights(sector: Optional[str] = None) -> dict:
    """Return CAS weights for the given sector (or defaults)."""
    if sector:
        s = sector.lower().strip()
        if s in SECTOR_WEIGHT_OVERRIDES:
            return SECTOR_WEIGHT_OVERRIDES[s]
    return DEFAULT_CAS_WEIGHTS


# ── 1. Composite Alpha Score (CAS) ────────────────────────────────────────────

def compute_cas(
    alpha_growth: float,        # α₁ normalised [−100, +100]
    alpha_margin: float,        # α₂
    alpha_consistency: float,   # α₃
    alpha_risk: float,          # α₄
    alpha_volatility: float,    # α₅
    alpha_credibility: float,   # α₆
    alpha_sentiment: float,     # α₇
    alpha_rel_strength: float,  # α₈
    sector: Optional[str] = None,
) -> dict:
    """
    Compute Composite Alpha Score (CAS).

    All alpha inputs must be pre-normalised to [−100, +100].
    Returns CAS clamped to [−100, +100] plus factor-level attribution.

    Parameters
    ----------
    alpha_* : float
        Each of the 8 normalised alpha scores.
    sector : str, optional
        Sector name for weight override (e.g. "banking", "nbfc").

    Returns
    -------
    dict with keys:
        cas           : float  —  Composite Alpha Score [−100, +100]
        weights       : dict   —  weights used
        contributions : dict   —  weighted contribution of each alpha
        sector        : str
    """
    weights = _get_weights(sector)

    alphas = {
        "growth":      alpha_growth,
        "margin":      alpha_margin,
        "consistency": alpha_consistency,
        "risk":        alpha_risk,
        "volatility":  alpha_volatility,
        "credibility": alpha_credibility,
        "sentiment":   alpha_sentiment,
        "rel_strength": alpha_rel_strength,
    }

    # Validate weights sum to 1.0 (hard guard)
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) >= 1e-6:
        raise ValueError(f"CAS weights must sum to 1.0, got {weight_sum:.6f} for sector={sector!r}")

    # Compute weighted contributions
    contributions = {
        key: weights[key] * alphas[key]
        for key in weights
    }
    cas_raw = sum(contributions.values())
    cas = _clamp(cas_raw)

    return {
        "cas": cas,
        "cas_raw": cas_raw,
        "weights": weights,
        "contributions": contributions,
        "sector": sector or "default",
    }


# ── 2. Data Confidence Index (DCI) ────────────────────────────────────────────

def compute_dci(
    available_fields: int,
    required_fields: int,
    years_available: int,
    target_years: int = 5,
    alpha_scores: Optional[list[float]] = None,  # list of the 8 normalised alphas
) -> dict:
    """
    Compute Data Confidence Index (DCI).

    DCI = 0.40·DataCoverage + 0.35·HistoryDepth + 0.25·AlphaAgreement

    Where:
      DataCoverage   = available_fields / required_fields          ∈ [0,1]
      HistoryDepth   = min(years_available / target_years, 1)      ∈ [0,1]
      AlphaAgreement = 1 − (std_dev of signed αᵢ / 100)           ∈ [0,1]

    Parameters
    ----------
    available_fields : int
        Number of financial data fields available for this company.
    required_fields : int
        Total required fields in the EREBUS data schema.
    years_available : int
        Years of historical data available.
    target_years : int
        Target history depth (default 5).
    alpha_scores : list[float]
        The 8 normalised alpha scores [−100, +100] for agreement calculation.

    Returns
    -------
    dict with keys:
        dci               : float  — [0, 1]
        dci_pct           : float  — displayed as percentage [0, 100]
        confidence_band   : str    — "HIGH" | "MODERATE" | "LOW"
        data_coverage     : float
        history_depth     : float
        alpha_agreement   : float
    """
    # DataCoverage
    data_coverage = available_fields / required_fields if required_fields > 0 else 0.0
    data_coverage = max(0.0, min(1.0, data_coverage))

    # HistoryDepth
    history_depth = min(years_available / target_years, 1.0)

    # AlphaAgreement
    if alpha_scores and len([a for a in alpha_scores if a is not None]) >= 2:
        valid_alphas = [a for a in alpha_scores if a is not None]
        std_alpha = statistics.stdev(valid_alphas)
        alpha_agreement = max(0.0, 1.0 - (std_alpha / 100.0))
    else:
        alpha_agreement = 0.5  # neutral if we can't compute

    dci = (
        0.40 * data_coverage +
        0.35 * history_depth +
        0.25 * alpha_agreement
    )
    dci = max(0.0, min(1.0, dci))
    dci_pct = round(dci * 100, 1)

    # Confidence band thresholds from architecture
    if dci >= 0.80:
        confidence_band = "HIGH"
    elif dci >= 0.50:
        confidence_band = "MODERATE"
    else:
        confidence_band = "LOW"

    return {
        "dci": dci,
        "dci_pct": dci_pct,
        "confidence_band": confidence_band,
        "data_coverage": data_coverage,
        "history_depth": history_depth,
        "alpha_agreement": alpha_agreement,
    }


# ── 3. Quant–Sentiment Divergence (QSD) ──────────────────────────────────────

def compute_qsd(
    alpha_growth: float,
    alpha_margin: float,
    alpha_consistency: float,
    alpha_risk: float,
    alpha_volatility: float,
    alpha_credibility: float,
    alpha_sentiment: float,
) -> dict:
    """
    Compute Quant–Sentiment Divergence (QSD).

    CAS_quant     = normalised(α₁·0.28 + α₂·0.28 + α₃·0.20 + α₄·0.14 + α₅·0.10)
    CAS_sentiment = normalised(α₆·0.60 + α₇·0.40)
    QSD = CAS_quant − CAS_sentiment

    QSD ∈ [−200, +200]
    |QSD| > 40 → triggers divergence flag

    Interpretation:
      QSD > +40  → "Narrative Lag"    (fundamentals > tone)
      |QSD| ≤ 40 → "Aligned"
      QSD < −40  → "Narrative Excess" (tone > fundamentals)

    Returns
    -------
    dict with keys:
        qsd               : float
        cas_quant         : float
        cas_sentiment     : float
        divergence_flag   : bool
        divergence_type   : str   — "NARRATIVE_LAG" | "ALIGNED" | "NARRATIVE_EXCESS"
        divergence_note   : str   — LLM instruction note if flagged
    """
    # CAS_quant: weighted sum of quantitative alphas, normalised to [−100, +100]
    raw_quant = (
        alpha_growth      * 0.28 +
        alpha_margin      * 0.28 +
        alpha_consistency * 0.20 +
        alpha_risk        * 0.14 +
        alpha_volatility  * 0.10
    )
    # Weights sum to 1.0 so output is already in [−100, +100] range
    cas_quant = _clamp(raw_quant)

    # CAS_sentiment: weighted sum of NLP-derived alphas
    raw_sentiment = (
        alpha_credibility * 0.60 +
        alpha_sentiment   * 0.40
    )
    cas_sentiment = _clamp(raw_sentiment)

    qsd = cas_quant - cas_sentiment
    divergence_flag = abs(qsd) > QSD_DIVERGENCE_THRESHOLD

    if qsd > QSD_DIVERGENCE_THRESHOLD:
        divergence_type = "NARRATIVE_LAG"
        divergence_note = (
            f"Note: A significant gap exists between fundamental signals "
            f"(CAS_quant: {cas_quant:.1f}) and management tone signals "
            f"(CAS_sentiment: {cas_sentiment:.1f}). This may indicate narrative lag — "
            f"fundamentals are outperforming tone. Potential underappreciated quality. "
            f"Analyst review of recent management commentary against reported results is advised."
        )
    elif qsd < -QSD_DIVERGENCE_THRESHOLD:
        divergence_type = "NARRATIVE_EXCESS"
        divergence_note = (
            f"Note: A significant gap exists between fundamental signals "
            f"(CAS_quant: {cas_quant:.1f}) and management tone signals "
            f"(CAS_sentiment: {cas_sentiment:.1f}). This may indicate narrative excess — "
            f"tone is outperforming fundamentals. Management may be over-projecting confidence. "
            f"Elevate scrutiny; Risk Alpha weight elevated by +5pp in CAS recalculation."
        )
    else:
        divergence_type = "ALIGNED"
        divergence_note = (
            "Quantitative and sentiment signals are broadly consistent. "
            "High-conviction CAS output. No divergence adjustment applied."
        )

    return {
        "qsd": round(qsd, 2),
        "cas_quant": round(cas_quant, 2),
        "cas_sentiment": round(cas_sentiment, 2),
        "divergence_flag": divergence_flag,
        "divergence_type": divergence_type,
        "divergence_note": divergence_note,
    }


# ── 4. Full Composite Output ──────────────────────────────────────────────────

def build_composite_output(
    normalised_alphas: dict,          # keys: growth, margin, consistency, risk,
                                      #       volatility, credibility, sentiment, rel_strength
    available_fields: int,
    required_fields: int,
    years_available: int,
    sector: Optional[str] = None,
) -> dict:
    """
    Convenience function: compute CAS + DCI + QSD in one call.

    Parameters
    ----------
    normalised_alphas : dict
        Must contain keys: growth, margin, consistency, risk,
        volatility, credibility, sentiment, rel_strength.
        All values must be pre-normalised to [−100, +100].
    available_fields, required_fields, years_available : int
        For DCI computation.
    sector : str, optional
        Sector for CAS weight override.

    Returns
    -------
    dict with top-level keys: cas_result, dci_result, qsd_result, summary
    """
    a = normalised_alphas

    cas_result = compute_cas(
        alpha_growth=a["growth"],
        alpha_margin=a["margin"],
        alpha_consistency=a["consistency"],
        alpha_risk=a["risk"],
        alpha_volatility=a["volatility"],
        alpha_credibility=a["credibility"],
        alpha_sentiment=a["sentiment"],
        alpha_rel_strength=a["rel_strength"],
        sector=sector,
    )

    alpha_score_list = [
        a["growth"], a["margin"], a["consistency"], a["risk"],
        a["volatility"], a["credibility"], a["sentiment"], a["rel_strength"],
    ]

    dci_result = compute_dci(
        available_fields=available_fields,
        required_fields=required_fields,
        years_available=years_available,
        alpha_scores=alpha_score_list,
    )

    qsd_result = compute_qsd(
        alpha_growth=a["growth"],
        alpha_margin=a["margin"],
        alpha_consistency=a["consistency"],
        alpha_risk=a["risk"],
        alpha_volatility=a["volatility"],
        alpha_credibility=a["credibility"],
        alpha_sentiment=a["sentiment"],
    )

    # High-level summary for LLM context injection
    summary = {
        "cas": cas_result["cas"],
        "cas_label": _cas_label(cas_result["cas"]),
        "dci_pct": dci_result["dci_pct"],
        "confidence_band": dci_result["confidence_band"],
        "qsd": qsd_result["qsd"],
        "divergence_type": qsd_result["divergence_type"],
        "divergence_flag": qsd_result["divergence_flag"],
        "top_alpha": _top_alpha(normalised_alphas),
        "bottom_alpha": _bottom_alpha(normalised_alphas),
    }

    return {
        "cas_result": cas_result,
        "dci_result": dci_result,
        "qsd_result": qsd_result,
        "summary": summary,
    }


def _cas_label(cas: float) -> str:
    if cas >= 60:  return "STRONG_POSITIVE"
    if cas >= 20:  return "POSITIVE"
    if cas >= -20: return "NEUTRAL"
    if cas >= -60: return "NEGATIVE"
    return "STRONG_NEGATIVE"


def _top_alpha(alphas: dict) -> str:
    return max(alphas, key=lambda k: alphas[k])


def _bottom_alpha(alphas: dict) -> str:
    return min(alphas, key=lambda k: alphas[k])
