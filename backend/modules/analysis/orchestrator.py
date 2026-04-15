"""
EREBUS — Analysis Orchestrator
================================
Single entry point that integrates all EREBUS modules.

Execution order (enforced):
    CompanyContext
        → Quant         (prices + financials → ratios, trends, volatility, risk)
        → Alpha         (enriched with Quant ratios — no duplicate computation)
        → Ranking       (uses CAS from alpha or mock)
        → Sentiment     (optional, never blocks)
        → [normal] → return structured output
        → [deep]   → RAG → LLM bundle → return structured + explanation

Return contract (always):
    {
        "mode":        "normal" | "deep",
        "company_id":  str,
        "data":        { ranking, quant, alpha, sentiment },
        "explanation": str | None   ← deep mode only
    }
"""

from __future__ import annotations
import logging
from enum import Enum
from typing import Dict, Any, Optional, List

from modules.ingestion.company_loader import load_company, CompanyDataError

logger = logging.getLogger(__name__)


# ── Analysis Mode ─────────────────────────────────────────────────────────────

class AnalysisMode(str, Enum):
    """
    Analysis depth selector.

    NORMAL: Returns pre-computed quant + alpha + ranking. Sub-2s. No LLM.
    DEEP:   Adds RAG retrieval + LLM narrative synthesis. Async, ~4min max.
    """
    NORMAL = "normal"
    DEEP   = "deep"


# ── COMPANY CONTEXT (single data object passed to all modules) ─────────────────

# _build_company_context() has been replaced by the real S3 loader.
# See modules/ingestion/company_loader.py → load_company()


# ── MODULE ADAPTERS ───────────────────────────────────────────────────────────
# Each adapter is isolated: exceptions are caught, None returned on failure.

def _run_quant(ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Step 1: Compute quantitative profile.
    Input:  prices + financials from CompanyContext.
    Output: { ratios, trends, volatility, risk }
    """
    try:
        from modules.quant import compute_quant_profile
        return compute_quant_profile(
            prices=ctx["prices"],
            financials=ctx["financials"],
        )
    except Exception as e:
        logger.warning(f"[quant] failed for {ctx['company_id']}: {e}")
        return None


def _run_alpha(
    ctx: Dict[str, Any],
    quant: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Step 2: Compute alpha signals.

    Enrichment rule: if Quant ratios are available, override the equivalent
    AlphaInput fields to avoid duplicate computation and ensure consistency.

    Input:  ctx.alpha_fields + quant.ratios (if available)
    Output: AlphaOutput with composite CAS signal
    """
    try:
        from modules.alpha import AlphaInput, run_all_alphas
        import dataclasses

        # Take a copy — never mutate CompanyContext
        fields = dict(ctx["alpha_fields"])

        # Enrich from Quant ratios (prevents recomputation divergence)
        if quant and quant.get("ratios"):
            r = quant["ratios"]
            _override(fields, "debt_to_equity",          r.get("debt_to_equity"))
            _override(fields, "roe",                     r.get("roe") or r.get("return_on_equity"))
            _override(fields, "interest_coverage_ratio", r.get("interest_coverage"))

        # Ensure required fields have defaults
        fields.setdefault("debt_to_equity", 0.5)
        fields.setdefault("roe", 0.12)
        fields.setdefault("interest_coverage_ratio", 2.0)

        # Strip any keys that AlphaInput doesn't declare — prevents TypeError
        valid_keys = {f.name for f in dataclasses.fields(AlphaInput)}
        clean_fields = {k: v for k, v in fields.items() if k in valid_keys}

        alpha_input = AlphaInput(**clean_fields)
        result = run_all_alphas(alpha_input)
        if isinstance(result, dict) and "alpha_fields" not in result:
            result["alpha_fields"] = ctx.get("alpha_fields", {})
        return result
    except Exception as e:
        logger.warning(f"[alpha] failed for {ctx['company_id']}: {e}")
        return None


def _run_ranking(
    ctx: Dict[str, Any],
    alpha: Optional[Dict[str, Any]],
    quant: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Step 3: Build ranking output from live alpha CAS + quant risk score.
    No mock data.
    """
    company_id = ctx["company_id"]
    try:
        cas        = _deep_get(alpha, ["composite", "cas"])
        dci        = _deep_get(alpha, ["composite", "dci"])
        qsd        = _deep_get(alpha, ["composite", "qsd"])
        normalised = (alpha or {}).get("normalised_alphas", {})
        raw_alphas = (alpha or {}).get("raw_alphas", {})

        # Use quant risk score (0-100) directly — authoritative source
        risk_score = None
        if quant and quant.get("risk"):
            risk_score = quant["risk"].get("overall_risk_score")

        sector = ctx.get("alpha_fields", {}).get("sector", "Unknown")

        return {
            "rank":       None,
            "cas":        round(cas, 2) if cas is not None else None,
            "dci":        round(dci, 2) if dci is not None else None,
            "qsd":        round(qsd, 2) if qsd is not None else None,
            "risk_score": round(risk_score, 1) if risk_score is not None else None,
            "sector":     sector,
            "signal_card": {"signals": normalised, "raw": raw_alphas},
            "note":       "Live score — single company, no universe ranking",
        }
    except Exception as e:
        logger.warning(f"[ranking] failed for {company_id}: {e}")
        return None


def _run_sentiment(ctx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Step 4: Sentiment analysis (always optional).
    In deep mode this output is injected into the LLM bundle.
    """
    try:
        from modules.sentiment import SentimentAnalyser
        analyser = SentimentAnalyser()
        text = ctx.get("text")
        if not text:
            return {
                "available":    True,
                "hedge_ratio":  None,
                "trajectory":   None,
                "note":         "No document text available for this company in MVP mode",
            }
        sentences = text.split(".")
        hedge = analyser.compute_hedge_ratio(sentences) if hasattr(analyser, "compute_hedge_ratio") else None
        return {
            "available":   True,
            "hedge_ratio": hedge,
            "trajectory":  None,
        }
    except ImportError:
        logger.info("[sentiment] module not available — skipping")
        return None
    except Exception as e:
        logger.warning(f"[sentiment] failed for {ctx['company_id']}: {e}")
        return None


def _run_rag(ctx: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Deep mode — Step 5: Retrieve relevant document chunks.
    Query is constructed from company_id (explicit, not magic string).
    """
    company_id = ctx["company_id"]
    query = f"{company_id} financial performance margins risk outlook"
    try:
        from modules.rag.query import RagRetriever
        retriever = RagRetriever()
        return retriever.retrieve_top_k(
            query=query,
            top_k=top_k,
            company_filter=company_id,
        )
    except Exception as e:
        logger.warning(f"[rag] failed for {company_id}: {e}")
        return []


def _run_llm(
    ctx:         Dict[str, Any],
    quant:       Optional[Dict[str, Any]],
    alpha:       Optional[Dict[str, Any]],
    ranking:     Optional[Dict[str, Any]],
    sentiment:   Optional[Dict[str, Any]],
    rag_chunks:  List[Dict[str, Any]],
    provider_name: str = "openai",
) -> Optional[str]:
    """
    Deep mode — Step 6: LLM narrative synthesis.

    Input bundle (full context):
        company_id + quant + alpha + ranking + sentiment + rag_documents

    Returns:
        Narrative string extracted from the first analysis (summary.text), or None.
    """
    company_id = ctx["company_id"]
    try:
        from modules.llm import analyze_company as llm_analyze, LLMProvider
        provider = LLMProvider(provider_name)
        doc_context = [c.get("chunk_text", "") for c in rag_chunks if c.get("chunk_text")]

        # Build quant profile for LLM (preserve all available data)
        llm_quant_profile = {}
        if quant:
            llm_quant_profile.update(quant)
        if alpha:
            llm_quant_profile["alpha"] = alpha
        if ranking:
            llm_quant_profile["ranking"] = ranking
        if sentiment:
            llm_quant_profile["sentiment"] = sentiment

        # Full LLM input bundle
        llm_result = llm_analyze(
            company_id=company_id,
            quant_profile=llm_quant_profile if llm_quant_profile else None,
            document_context=doc_context,
            provider=provider,
        )

        # Extract narrative text for the explanation field
        return _deep_get(llm_result, ["analyses", "summary", "text"])
    except Exception as e:
        logger.warning(f"[llm] failed for {company_id}: {e}")
        return None


# ── MAIN ORCHESTRATOR ─────────────────────────────────────────────────────────

def analyze_company(
    company_id:   str,
    mode:         str = "normal",
    llm_provider: str = "openai",
) -> Dict[str, Any]:
    """
    Unified company analysis — EREBUS integration layer.

    Args:
        company_id:   Company ticker or identifier (e.g. "RELIANCE", "TCS")
        mode:         "normal" or "deep"
        llm_provider: "openai" | "anthropic" | "ollama"  (deep mode only)

    Returns (always consistent):
        {
            "mode":        "normal" | "deep",
            "company_id":  str,
            "data": {
                "ranking":   dict | None,
                "quant":     dict | None,
                "alpha":     dict | None,
                "sentiment": dict | None,
            },
            "explanation": str | None   ← populated in deep mode only
        }
    """
    mode = mode.lower().strip()
    if mode not in ("normal", "deep"):
        raise ValueError(f"mode must be 'normal' or 'deep', got '{mode}'")

    logger.info(f"[orchestrator] {company_id} | mode={mode}")

    # ── Load company data from S3 (replaces _build_company_context mock) ───────
    try:
        ctx = load_company(company_id)
    except CompanyDataError as e:
        logger.error("[orchestrator] Company data load failed for %s: %s", company_id, e)
        raise ValueError(str(e))   # router maps ValueError → HTTP 400

    # ── Core pipeline (Quant → Alpha → Ranking → Sentiment) ──────────────────
    quant     = _run_quant(ctx)                       # Step 1
    alpha     = _run_alpha(ctx, quant)               # Step 2
    ranking   = _run_ranking(ctx, alpha, quant)      # Step 3 — quant risk score
    sentiment = _run_sentiment(ctx)                  # Step 4

    structured = {
        "ranking":   ranking,
        "quant":     quant,
        "alpha":     alpha,
        "sentiment": sentiment,
    }

    # ── Data quality envelope (from loader) ──────────────────────────────────
    dq       = ctx.get("financials", {}).get("_data_quality", {})
    warnings = list(dq.get("warnings", []))
    # Add run-time warnings when a module returned None
    if quant is None:
        warnings.append("Quantitative analysis unavailable — check server logs")
    if alpha is None:
        warnings.append("Alpha signals unavailable — check server logs")
    if ranking is None:
        warnings.append("Ranking/CAS score unavailable — check server logs")
    if ctx.get("text") is None:
        warnings.append("No document text — sentiment analysis limited")

    # ── Result scaffold (always same shape) ─────────────────────────────────
    result: Dict[str, Any] = {
        "mode":         mode,
        "company_id":   company_id,
        "data":         structured,
        "explanation":  None,         # populated in deep mode
        "data_quality": dq,
        "warnings":     warnings,
        "confidence":   _compute_confidence(dq, structured),
    }

    # ── Deep mode: RAG + LLM ─────────────────────────────────────────────────
    if mode == "deep":
        rag_chunks  = _run_rag(ctx)                          # Step 5
        explanation = _run_llm(                              # Step 6
            ctx, quant, alpha, ranking, sentiment,
            rag_chunks, llm_provider,
        )
        result["explanation"] = explanation
        result["rag_chunks"]  = rag_chunks   # include for transparency

    logger.info(f"[orchestrator] done: {company_id} ({mode})")
    return result


# ── UTILITIES ─────────────────────────────────────────────────────────────────

def _compute_confidence(dq: dict, data: dict) -> float:
    """
    Data-completeness confidence score (0.0–1.0).

    Starts from the loader's data_quality score, then penalises further
    when the analysis modules themselves returned None (e.g. quant failed,
    alpha failed).
    """
    score = float(dq.get("score", 0.5))
    if data.get("alpha") is None:
        score = max(0.0, score - 0.15)   # alpha missing → big signal gap
    if data.get("quant") is None:
        score = max(0.0, score - 0.10)   # quant missing → moderate gap
    if data.get("ranking") is None:
        score = max(0.0, score - 0.05)   # ranking missing → minor gap
    return round(score, 2)


def _override(d: dict, key: str, value: Any) -> None:
    """Set key in dict only if value is not None."""
    if value is not None:
        d[key] = value


def _deep_get(obj: Any, keys: List[str], default: Any = None) -> Any:
    """Safe nested dict access: _deep_get(d, ['a', 'b', 'c']) = d['a']['b']['c']."""
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k, default)
        if obj is None:
            return default
    return obj