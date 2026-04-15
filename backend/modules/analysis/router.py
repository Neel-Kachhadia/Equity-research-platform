"""
Analysis Router — GET /analyze
================================
FastAPI endpoint for dual-mode company analysis.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from .orchestrator import analyze_company

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.get(
    "",
    summary="Analyze a company (normal or deep mode)",
    response_description=(
        "Structured analysis including ranking, quant, alpha, and "
        "optionally LLM narrative (deep mode)."
    ),
)
def analyze(
    company_id: str = Query(
        ...,
        description="Company identifier, e.g. RELIANCE or TCS",
    ),
    mode: str = Query(
        "normal",
        description="Analysis mode: 'normal' (structured) or 'deep' (+ RAG + LLM narrative)",
    ),
    llm_provider: str = Query(
        "gemini",
        description="LLM provider for deep mode: gemini | openai | anthropic | ollama | bedrock",
    ),
):
    """
    ## GET /analyze

    Analyze a company using the full EREBUS engine.

    ### Normal mode
    Fast structured output: ranking position, quantitative profile, alpha signals.
    No LLM or RAG involved.

    ### Deep mode
    All of normal mode **plus** RAG document retrieval and an LLM-generated
    narrative explanation via the configured provider.

    ### Example requests
    ```
    GET /analyze?company_id=RELIANCE&mode=normal
    GET /analyze?company_id=TCS&mode=deep&llm_provider=openai
    GET /analyze?company_id=HDFC&mode=deep&llm_provider=ollama
    ```

    ### Response shape (always consistent)
    ```json
    {
        "mode":        "normal | deep",
        "company_id":  "RELIANCE",
        "data": {
            "ranking":   { ... },
            "quant":     { ... },
            "alpha":     { ... },
            "sentiment": { ... }
        },
        "explanation": "string | null"
    }
    ```
    """
    if mode not in ("normal", "deep"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{mode}'. Must be 'normal' or 'deep'.",
        )
    if llm_provider not in ("gemini", "openai", "anthropic", "ollama", "bedrock"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid llm_provider '{llm_provider}'. Must be gemini | openai | anthropic | ollama | bedrock.",
        )

    try:
        result = analyze_company(
            company_id=company_id,
            mode=mode,
            llm_provider=llm_provider,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Auto-record in user_analytics (best-effort)
    try:
        from modules.analytics.router import record_session
        record_session(
            "score",
            f"{company_id} FY Analysis",
            f"Mode: {'deep' if mode == 'deep' else 'normal'} · {llm_provider}",
            company_id,
        )
    except Exception:
        pass

    return result


