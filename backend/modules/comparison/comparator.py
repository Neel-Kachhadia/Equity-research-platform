"""
EREBUS — Company Comparator
============================
Reuses analyze_company() output. Never recomputes quant/alpha.

Dimensions & weights:
    Performance  30%   (revenue_growth, profit_margin, roe, net_income)
    Alpha        25%   (momentum, value, quality, sentiment, earnings_revision)
    Risk         25%   (risk_score[inverted], volatility[inv], drawdown[inv])
    Technical    20%   (rsi_score, trend_score, macd_score)
"""

from __future__ import annotations
import logging
import concurrent.futures
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Dimension weights ─────────────────────────────────────────────────────────
WEIGHTS = {
    "performance": 0.30,
    "alpha":       0.25,
    "risk":        0.25,
    "technical":   0.20,
}


# ── Safe getters ──────────────────────────────────────────────────────────────

def _g(d: Any, *keys, default=None):
    """Nested safe-get."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d


def _safe_float(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


# ── Metric extraction ─────────────────────────────────────────────────────────

def extract_metrics(analysis: dict, financials: dict) -> dict:
    """
    Build a flat metrics dict from analyze_company() output + raw financials.

    Returns:
        {
          performance: { revenue, net_income, revenue_growth, profit_margin, roe },
          risk:        { risk_score, volatility, max_drawdown },
          alpha:       { momentum, value, quality, sentiment, earnings_revision, cas },
          technical:   { rsi, trend, macd_signal },
        }
    """
    data     = analysis.get("data", {})
    ranking  = data.get("ranking") or {}
    quant    = data.get("quant")   or {}
    alpha    = data.get("alpha")   or {}

    # Quant sub-dicts
    ratios   = quant.get("ratios")  or {}
    risk_q   = quant.get("risk")    or {}
    trends_q = quant.get("trends")  or {}
    vol_q    = quant.get("volatility") or {}

    # Alpha sub-dicts
    norm_a   = alpha.get("normalised_alphas") or {}
    raw_a    = alpha.get("raw_alphas")        or {}
    comp_a   = alpha.get("composite")         or {}

    # Raw financials from company_loader
    fin      = financials.get("financials") or {}
    af       = financials.get("alpha_fields") or {}

    # ── Performance ──────────────────────────────────────────────────────────
    rev_series = af.get("revenue_series") or []
    revenue    = _safe_float(fin.get("revenue") or (rev_series[-1] if rev_series else None))
    net_income = _safe_float(fin.get("net_income"))

    # revenue_growth from quant or compute from series
    rev_growth = _safe_float(
        ratios.get("revenue_growth")
        or ratios.get("revenue_growth_yoy")
    )
    if rev_growth is None and len(rev_series) >= 2 and rev_series[0]:
        rev_growth = round((rev_series[-1] / rev_series[0] - 1) * 100, 2)

    profit_margin = _safe_float(
        ratios.get("net_profit_margin")
        or ratios.get("profit_margin")
        or raw_a.get("margin")
    )
    if profit_margin is None and revenue and net_income:
        profit_margin = round(net_income / revenue * 100, 2)

    roe = _safe_float(ratios.get("return_on_equity") or ratios.get("roe"))

    # ── Risk ─────────────────────────────────────────────────────────────────
    risk_score = _safe_float(
        ranking.get("risk_score")
        or risk_q.get("overall_risk_score")
        or risk_q.get("risk_score")
    )
    volatility = _safe_float(
        vol_q.get("annual_volatility")
        or vol_q.get("volatility")
        or risk_q.get("volatility")
    )
    max_drawdown = _safe_float(
        risk_q.get("max_drawdown")
        or vol_q.get("max_drawdown")
    )

    # ── Alpha signals ─────────────────────────────────────────────────────────
    cas = _safe_float(
        ranking.get("cas")
        or _g(comp_a, "cas")
    )

    def _alpha_val(key: str) -> Optional[float]:
        """Try normalised, then raw, then ranking signal_card."""
        v = norm_a.get(key)
        if v is None:
            v = raw_a.get(key)
        if v is None:
            v = _g(ranking, "signal_card", "signals", key)
        return _safe_float(v)

    # ── Technicals ────────────────────────────────────────────────────────────
    rsi = _safe_float(
        trends_q.get("rsi")
        or risk_q.get("rsi")
        or raw_a.get("rsi")
    )
    trend_raw = (
        trends_q.get("sma_trend")
        or trends_q.get("trend")
        or trends_q.get("direction")
        or ""
    )
    # Convert trend text → numeric score (0-1)
    trend_score = _trend_to_score(str(trend_raw).lower())

    macd_raw = (
        trends_q.get("macd_signal")
        or trends_q.get("macd")
        or raw_a.get("macd_signal")
    )
    macd_score = _macd_to_score(macd_raw)

    return {
        "performance": {
            "revenue":       revenue,
            "net_income":    net_income,
            "revenue_growth": rev_growth,
            "profit_margin": profit_margin,
            "roe":           roe,
        },
        "risk": {
            "risk_score":   risk_score,
            "volatility":   volatility,
            "max_drawdown": max_drawdown,
        },
        "alpha": {
            "momentum":          _alpha_val("momentum"),
            "value":             _alpha_val("value"),
            "quality":           _alpha_val("quality"),
            "sentiment":         _alpha_val("sentiment"),
            "earnings_revision": _alpha_val("earnings_revision"),
            "cas":               cas,
        },
        "technical": {
            "rsi":          rsi,
            "trend":        trend_raw or None,
            "trend_score":  trend_score,
            "macd_signal":  macd_raw,
            "macd_score":   macd_score,
        },
    }


def _trend_to_score(trend: str) -> Optional[float]:
    if "up" in trend or "bull" in trend or "positive" in trend:
        return 0.75
    if "down" in trend or "bear" in trend or "negative" in trend:
        return 0.25
    if "neutral" in trend or "flat" in trend or "side" in trend:
        return 0.50
    return None


def _macd_to_score(macd) -> Optional[float]:
    if macd is None:
        return None
    if isinstance(macd, str):
        s = macd.lower()
        if "buy" in s or "bullish" in s or "positive" in s:
            return 0.75
        if "sell" in s or "bearish" in s or "negative" in s:
            return 0.25
        return 0.50
    try:
        v = float(macd)
        # MACD numeric: positive = bullish (cap at ±0.25 → [0.25, 0.75])
        return max(0.0, min(1.0, 0.50 + v * 2))
    except (TypeError, ValueError):
        return None


# ── Normalisation & scoring ───────────────────────────────────────────────────

def _normalise_pair(a: Optional[float], b: Optional[float], higher_is_better: bool = True):
    """
    Return (score_a, score_b) in [0, 1].
    Missing values → 0.50 (neutral).
    """
    if a is None and b is None:
        return 0.50, 0.50
    if a is None:
        return 0.40, 0.60 if higher_is_better else (0.60, 0.40)
    if b is None:
        return 0.60, 0.40 if higher_is_better else (0.40, 0.60)

    lo, hi = min(a, b), max(a, b)
    if lo == hi:
        return 0.50, 0.50
    span = hi - lo

    # Relative scoring — winner gets 1.0, loser scaled
    if higher_is_better:
        sa = (a - lo) / span
        sb = (b - lo) / span
    else:
        sa = 1.0 - (a - lo) / span
        sb = 1.0 - (b - lo) / span

    # Compress to [0.25, 0.75] to avoid extreme 0/1
    sa = 0.25 + sa * 0.50
    sb = 0.25 + sb * 0.50
    return round(sa, 3), round(sb, 3)


def _category_scores(m_a: dict, m_b: dict) -> dict[str, tuple[float, float]]:
    """
    Returns per-category (score_a, score_b) tuples (0-1).
    """
    scores = {}

    # ── Performance ──────────────────────────────────────────────────────────
    pa, pb = m_a["performance"], m_b["performance"]
    p_pairs = [
        _normalise_pair(pa.get("revenue_growth"), pb.get("revenue_growth"), True),
        _normalise_pair(pa.get("profit_margin"),  pb.get("profit_margin"),  True),
        _normalise_pair(pa.get("roe"),            pb.get("roe"),            True),
        _normalise_pair(pa.get("net_income"),     pb.get("net_income"),     True),
    ]
    scores["performance"] = _avg_pairs(p_pairs)

    # ── Risk (lower = better → invert) ───────────────────────────────────────
    ra, rb = m_a["risk"], m_b["risk"]
    r_pairs = [
        _normalise_pair(ra.get("risk_score"),   rb.get("risk_score"),   False),
        _normalise_pair(ra.get("volatility"),   rb.get("volatility"),   False),
        _normalise_pair(ra.get("max_drawdown"), rb.get("max_drawdown"), False),
    ]
    scores["risk"] = _avg_pairs(r_pairs)

    # ── Alpha ─────────────────────────────────────────────────────────────────
    aa, ab = m_a["alpha"], m_b["alpha"]
    alpha_keys = ["momentum", "value", "quality", "sentiment", "earnings_revision", "cas"]
    al_pairs = [_normalise_pair(aa.get(k), ab.get(k), True) for k in alpha_keys]
    scores["alpha"] = _avg_pairs(al_pairs)

    # ── Technical ─────────────────────────────────────────────────────────────
    ta, tb = m_a["technical"], m_b["technical"]
    # RSI: 50 is neutral target; closer to 55-65 = bullish
    rsi_sa, rsi_sb = _rsi_score_pair(ta.get("rsi"), tb.get("rsi"))
    t_pairs = [
        (rsi_sa, rsi_sb),
        _normalise_pair(ta.get("trend_score"), tb.get("trend_score"), True),
        _normalise_pair(ta.get("macd_score"),  tb.get("macd_score"),  True),
    ]
    scores["technical"] = _avg_pairs(t_pairs)

    return scores


def _avg_pairs(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    valid = [(sa, sb) for sa, sb in pairs if sa != 0.50 or sb != 0.50]
    if not valid:
        valid = pairs
    sa = sum(s[0] for s in valid) / len(valid)
    sb = sum(s[1] for s in valid) / len(valid)
    return round(sa, 3), round(sb, 3)


def _rsi_score_pair(rsi_a, rsi_b) -> tuple[float, float]:
    """Score RSI by proximity to the 'ideal' bullish zone 55-65."""
    def _rsi_proximity(rsi):
        if rsi is None:
            return 0.50
        r = float(rsi)
        if 55 <= r <= 65:
            return 0.75
        if r > 70 or r < 30:
            return 0.25   # overbought / oversold
        if r >= 45:
            return 0.60
        return 0.40
    sa, sb = _rsi_proximity(rsi_a), _rsi_proximity(rsi_b)
    # Relative within pair
    if sa == sb:
        return 0.50, 0.50
    if sa > sb:
        return 0.65, 0.35
    return 0.35, 0.65


def _determine_category_winner(score_a: float, score_b: float, id_a: str, id_b: str) -> str:
    if abs(score_a - score_b) < 0.03:
        return "tie"
    return id_a if score_a > score_b else id_b


def _compute_overall_winner(cat_scores: dict, id_a: str, id_b: str) -> tuple[str, float]:
    total_a = total_b = 0.0
    for cat, (sa, sb) in cat_scores.items():
        w = WEIGHTS.get(cat, 0.25)
        total_a += sa * w
        total_b += sb * w
    if abs(total_a - total_b) < 0.015:
        winner, confidence = "tie", 0.50
    else:
        winner = id_a if total_a > total_b else id_b
        diff   = abs(total_a - total_b)
        confidence = round(min(0.95, 0.50 + diff * 3), 2)
    return winner, confidence


def _key_differences(m_a: dict, m_b: dict, id_a: str, id_b: str) -> list[str]:
    diffs = []

    pm_a = m_a["performance"].get("profit_margin")
    pm_b = m_b["performance"].get("profit_margin")
    if pm_a is not None and pm_b is not None and abs(pm_a - pm_b) > 1:
        leader = id_a if pm_a > pm_b else id_b
        diffs.append(f"{leader} has stronger profit margin ({max(pm_a,pm_b):.1f}% vs {min(pm_a,pm_b):.1f}%)")

    rg_a = m_a["performance"].get("revenue_growth")
    rg_b = m_b["performance"].get("revenue_growth")
    if rg_a is not None and rg_b is not None and abs(rg_a - rg_b) > 2:
        leader = id_a if rg_a > rg_b else id_b
        diffs.append(f"{leader} shows faster revenue growth ({max(rg_a,rg_b):.1f}% vs {min(rg_a,rg_b):.1f}%)")

    rs_a = m_a["risk"].get("risk_score")
    rs_b = m_b["risk"].get("risk_score")
    if rs_a is not None and rs_b is not None and abs(rs_a - rs_b) > 3:
        safer = id_a if rs_a < rs_b else id_b
        diffs.append(f"{safer} carries a lower risk profile (score {min(rs_a,rs_b):.0f} vs {max(rs_a,rs_b):.0f}/100)")

    cas_a = m_a["alpha"].get("cas")
    cas_b = m_b["alpha"].get("cas")
    if cas_a is not None and cas_b is not None and abs(cas_a - cas_b) > 0.05:
        leader = id_a if cas_a > cas_b else id_b
        diffs.append(f"Alpha (CAS) favours {leader} ({max(cas_a,cas_b):.2f} vs {min(cas_a,cas_b):.2f})")

    mom_a = m_a["alpha"].get("momentum")
    mom_b = m_b["alpha"].get("momentum")
    if mom_a is not None and mom_b is not None and abs(mom_a - mom_b) > 0.05:
        leader = id_a if mom_a > mom_b else id_b
        diffs.append(f"Price momentum favours {leader}")

    return diffs or ["Both companies show comparable metrics across dimensions"]


def _build_chart_data(id_a: str, id_b: str, m_a: dict, m_b: dict) -> dict:
    labels = [
        "Revenue Growth", "Profit Margin", "ROE",
        "CAS", "Momentum", "Quality",
        "Risk (inv)", "RSI Score",
    ]

    def _pick(*path_vals):
        return path_vals[0] if path_vals else None

    def _norm_rev(v, lo=0, hi=30):
        if v is None: return 0.5
        return max(0, min(1, (v - lo) / (hi - lo))) if hi != lo else 0.5

    def _norm_margin(v, lo=0, hi=30):
        return _norm_rev(v, lo, hi)

    def _norm_roe(v, lo=0, hi=40):
        return _norm_rev(v, lo, hi)

    def _norm_cas(v):
        if v is None: return 0.5
        return max(0, min(1, (v + 1) / 2))

    def _norm_alpha(v):
        return max(0, min(1, float(v))) if v is not None else 0.5

    def _norm_risk_inv(v):
        if v is None: return 0.5
        return max(0, min(1, 1 - v / 100))

    def _norm_rsi(v):
        if v is None: return 0.5
        return max(0, min(1, v / 100))

    def _row(m):
        p, a, r, t = m["performance"], m["alpha"], m["risk"], m["technical"]
        return [
            _norm_rev(p.get("revenue_growth")),
            _norm_margin(p.get("profit_margin")),
            _norm_roe(p.get("roe")),
            _norm_cas(a.get("cas")),
            _norm_alpha(a.get("momentum")),
            _norm_alpha(a.get("quality")),
            _norm_risk_inv(r.get("risk_score")),
            _norm_rsi(t.get("rsi")),
        ]

    return {
        "labels":    labels,
        "company_a": [round(v, 3) for v in _row(m_a)],
        "company_b": [round(v, 3) for v in _row(m_b)],
        "ids":       [id_a, id_b],
    }


# ── Public API ────────────────────────────────────────────────────────────────

def compare_companies(company_a: str, company_b: str) -> dict:
    """
    Main comparison function.

    1. Parallel analysis via analyze_company() + load_company()
    2. Extract → normalise → score
    3. Build full comparison response
    """
    from modules.analysis.orchestrator import analyze_company
    from modules.ingestion.company_loader import load_company

    # Preserve exact S3 folder case — forcing .upper() would break lookups for
    # folders like "HCL Technologies/" when the incoming ticker is "HCL Technologies".
    id_a = company_a.strip()
    id_b = company_b.strip()

    if id_a.upper() == id_b.upper():
        raise ValueError("Cannot compare a company with itself")

    # ── Parallel fetch ────────────────────────────────────────────────────────
    results: dict = {}
    errors:  dict = {}

    def _fetch(cid):
        try:
            analysis = analyze_company(cid, mode="normal")
            fin      = load_company(cid)
            return cid, analysis, fin
        except Exception as e:
            logger.warning("[compare] fetch failed for %s: %s", cid, e)
            return cid, None, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(_fetch, c): c for c in (id_a, id_b)}
        for fut in concurrent.futures.as_completed(futures):
            cid, analysis, fin = fut.result()
            if analysis is None:
                errors[cid] = "Failed to load company data"
            else:
                results[cid] = (analysis, fin or {})

    # ── Partial response if one company failed ────────────────────────────────
    if id_a not in results and id_b not in results:
        raise ValueError(f"Both companies failed to load. Neither {id_a} nor {id_b} has parseable financial data (.xlsx/.json) in S3.")

    if id_a not in results:
        return {"error": f"Could not load {id_a}: {errors.get(id_a)}", "partial": True,
                "available": id_b}
    if id_b not in results:
        return {"error": f"Could not load {id_b}: {errors.get(id_b)}", "partial": True,
                "available": id_a}

    analysis_a, fin_a = results[id_a]
    analysis_b, fin_b = results[id_b]

    # ── Extract metrics ───────────────────────────────────────────────────────
    m_a = extract_metrics(analysis_a, fin_a)
    m_b = extract_metrics(analysis_b, fin_b)

    # ── Score ─────────────────────────────────────────────────────────────────
    cat_scores = _category_scores(m_a, m_b)

    category_winners = {
        cat: _determine_category_winner(sa, sb, id_a, id_b)
        for cat, (sa, sb) in cat_scores.items()
    }

    winner, confidence = _compute_overall_winner(cat_scores, id_a, id_b)
    key_diffs = _key_differences(m_a, m_b, id_a, id_b)

    # ── Build flat metrics dict ───────────────────────────────────────────────
    def _metric_entry(key, *path_a, path_b=None, invert=False):
        va = m_a
        for k in path_a: va = (va or {}).get(k)
        pb = path_b or path_a
        vb = m_b
        for k in pb: vb = (vb or {}).get(k)
        return {id_a: va, id_b: vb}

    metrics = {
        "revenue":          {id_a: m_a["performance"].get("revenue"),          id_b: m_b["performance"].get("revenue")},
        "net_income":       {id_a: m_a["performance"].get("net_income"),        id_b: m_b["performance"].get("net_income")},
        "revenue_growth":   {id_a: m_a["performance"].get("revenue_growth"),   id_b: m_b["performance"].get("revenue_growth")},
        "profit_margin":    {id_a: m_a["performance"].get("profit_margin"),     id_b: m_b["performance"].get("profit_margin")},
        "roe":              {id_a: m_a["performance"].get("roe"),               id_b: m_b["performance"].get("roe")},
        "risk_score":       {id_a: m_a["risk"].get("risk_score"),               id_b: m_b["risk"].get("risk_score")},
        "volatility":       {id_a: m_a["risk"].get("volatility"),               id_b: m_b["risk"].get("volatility")},
        "max_drawdown":     {id_a: m_a["risk"].get("max_drawdown"),             id_b: m_b["risk"].get("max_drawdown")},
        "momentum":         {id_a: m_a["alpha"].get("momentum"),                id_b: m_b["alpha"].get("momentum")},
        "value":            {id_a: m_a["alpha"].get("value"),                   id_b: m_b["alpha"].get("value")},
        "quality":          {id_a: m_a["alpha"].get("quality"),                 id_b: m_b["alpha"].get("quality")},
        "sentiment":        {id_a: m_a["alpha"].get("sentiment"),               id_b: m_b["alpha"].get("sentiment")},
        "earnings_revision":{id_a: m_a["alpha"].get("earnings_revision"),       id_b: m_b["alpha"].get("earnings_revision")},
        "cas":              {id_a: m_a["alpha"].get("cas"),                     id_b: m_b["alpha"].get("cas")},
        "rsi":              {id_a: m_a["technical"].get("rsi"),                 id_b: m_b["technical"].get("rsi")},
        "trend":            {id_a: m_a["technical"].get("trend"),               id_b: m_b["technical"].get("trend")},
        "macd_signal":      {id_a: m_a["technical"].get("macd_signal"),         id_b: m_b["technical"].get("macd_signal")},
    }

    # Strip None-only rows for cleaner output
    metrics = {k: v for k, v in metrics.items() if any(x is not None for x in v.values())}

    # ── Aggregate data quality from both companies ────────────────────────────
    dq_a = analysis_a.get("data_quality") or {}
    dq_b = analysis_b.get("data_quality") or {}

    combined_warnings = (
        [f"[{id_a}] {w}" for w in (dq_a.get("warnings") or [])]
        + [f"[{id_b}] {w}" for w in (dq_b.get("warnings") or [])]
    )

    # Comparison confidence: average of both companies' DQ scores
    # Falls back to 0.5 if either is absent (unknown quality)
    score_a = float(dq_a.get("score", 0.5))
    score_b = float(dq_b.get("score", 0.5))
    comparison_confidence = round((score_a + score_b) / 2, 2)

    return {
        "company_a": id_a,
        "company_b": id_b,
        "summary": {
            "winner":                winner,
            "comparison_confidence": confidence,   # how decisive the score difference is
            "category_winners":      category_winners,
        },
        "scores": {
            cat: {id_a: round(sa, 3), id_b: round(sb, 3)}
            for cat, (sa, sb) in cat_scores.items()
        },
        "metrics":    metrics,
        "chart_data": _build_chart_data(id_a, id_b, m_a, m_b),
        "key_differences": key_diffs,
        # Data quality transparency
        "data_quality": {id_a: dq_a, id_b: dq_b},
        "warnings":     combined_warnings,
        "confidence":   comparison_confidence,   # data-completeness confidence
        # raw metrics for LLM explainer
        "_raw": {"a": m_a, "b": m_b},
    }
