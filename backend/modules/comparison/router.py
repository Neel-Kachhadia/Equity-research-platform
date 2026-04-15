"""
EREBUS — Comparison Router
===========================
GET /compare?company_a=TCS&company_b=INFY&mode=deep

Response shape:
  {
    company_a, company_b,
    summary   : { winner, confidence, category_winners },
    scores    : { performance, risk, alpha, technical },
    metrics   : { revenue, net_income, ... },
    chart_data: { labels, company_a[], company_b[], ids[] },
    key_differences: [...],
    explanation: str | null,
  }
"""

from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.get("", summary="Compare two companies across performance, risk, alpha & technicals")
def compare(
    company_a: str = Query(..., description="Ticker for company A, e.g. TCS"),
    company_b: str = Query(..., description="Ticker for company B, e.g. INFY"),
    mode: str = Query("normal", description="'normal' — no LLM explanation | 'deep' — adds Groq narrative"),
):
    """
    GET /compare?company_a=TCS&company_b=INFY&mode=deep

    Runs parallel normal-mode analysis for both companies,
    scores them on 4 weighted dimensions, and (if mode=deep)
    generates a Groq LLM explanation.
    """
    # Preserve the exact casing from the S3 folder name.
    # .upper() here would corrupt lookups for folders like "HCL Technologies/".
    id_a = company_a.strip()
    id_b = company_b.strip()

    if id_a.upper() == id_b.upper():
        raise HTTPException(400, detail="Cannot compare a company with itself.")

    if mode not in ("normal", "deep"):
        raise HTTPException(400, detail="mode must be 'normal' or 'deep'.")

    # ── Run comparison ────────────────────────────────────────────────────────
    try:
        from modules.comparison.comparator import compare_companies
        result = compare_companies(id_a, id_b)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        logger.error("[compare] comparison failed: %s", e, exc_info=True)
        raise HTTPException(500, detail=f"Comparison failed: {e}")

    # ── Partial result handling ───────────────────────────────────────────────
    if result.get("partial"):
        failed    = result.get("error", "One company failed to load")
        available = result.get("available")
        raise HTTPException(
            400,
            detail={
                "message":   failed,
                "available": available,
                "hint":      (
                    "Check that this company exists in S3 and has an .xlsx or .json data file. "
                    "Use GET /companies to see the list of analysable companies."
                ),
            },
        )

    # ── Strip internal raw data ───────────────────────────────────────────────
    raw = result.pop("_raw", {})

    # ── LLM explanation (deep mode only) ─────────────────────────────────────
    explanation: str | None = None
    if mode == "deep":
        try:
            from modules.comparison.llm_explainer import generate_explanation
            explanation = generate_explanation(
                id_a      = id_a,
                id_b      = id_b,
                summary   = result["summary"],
                metrics   = result["metrics"],
                key_diffs = result["key_differences"],
            )
        except Exception as e:
            logger.warning("[compare] LLM explanation failed: %s", e)

    result["explanation"] = explanation
    return result
