"""
EREBUS · Chat Router — POST /chat
===================================
Handles freeform research questions. Pipeline:

  1. Extract company mentions from the question (simple regex)
  2. If a known company is detected → load its CompanyContext from S3
  3. Build a context-rich system prompt with live financials + alpha signals
  4. Send to the configured LLM provider
  5. Return structured {answer, sources, company_id, model}

If no company is matched or S3 fails, falls back to
LLM-only mode with a generic financial analyst system prompt.
"""

from __future__ import annotations
import os
import re
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from modules.ingestion.company_loader import load_company

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Known company aliases ─────────────────────────────────────────────────────

_COMPANY_ALIASES: dict[str, str] = {
    # IT — large-cap
    "tcs": "TCS", "tata consultancy": "TCS",
    "infosys": "Infosys", "infy": "Infosys",
    "wipro": "Wipro",
    "hcltech": "HCL_Tech", "hcl tech": "HCL_Tech", "hcl technologies": "HCL_Tech",
    "techm": "TechM", "tech mahindra": "TechM",
    # IT — EREBUS mid-cap universe
    "emudhra": "eMudhra", "e mudhra": "eMudhra",
    "ksolves": "Ksolves", "k solves": "Ksolves",
    "newgen": "Newgen", "newgen software": "Newgen",
    "saksoft": "Saksoft",
    "intellect": "Intellect", "intellect design": "Intellect", "intellect design arena": "Intellect",
    "ramco": "Ramco", "ramco systems": "Ramco",
    # Finance
    "hdfc bank": "HDFC_Bank", "hdfcbank": "HDFC_Bank",
    "icici bank": "ICICI_Bank", "icicibank": "ICICI_Bank",
    "sbi": "SBI", "state bank": "SBI",
    "axis bank": "Axis_Bank", "axisbank": "Axis_Bank",
    "kotak": "Kotak_Bank", "kotak mahindra": "Kotak_Bank",
    # Consumer / Diversified
    "reliance": "Reliance", "ril": "Reliance",
    "asian paints": "Asian_Paints",
    "titan": "Titan",
    "bajaj finance": "Bajaj_Finance",
    "hindustan unilever": "HUL", "hul": "HUL",
}


def _extract_companies(question: str) -> list[str]:
    """Return all known company_ids found in the question."""
    q = question.lower()
    found: list[str] = []
    
    # 1. Full alias match
    for alias, cid in _COMPANY_ALIASES.items():
        pattern = r'\b' + re.escape(alias.lower()) + r'\b'
        if re.search(pattern, q) and cid not in found:
            found.append(cid)
            
    # 2. Bare ticker pattern
    match = re.search(r"\b([A-Z]{2,10})\b", question)
    if match:
        upper = match.group(1).upper()
        for alias, cid in _COMPANY_ALIASES.items():
            if (alias.upper() == upper or cid.upper() == upper) and cid not in found:
                found.append(cid)
                
    return found


_FY_PATTERNS = [
    # Match "FY2024", "FY 24", "FY24"
    re.compile(r"\bFY\s*(?:20)?(\d{2})\b", re.I),
    # Match "financial year 2024", "year 2024"
    re.compile(r"\b(?:financial\s+year|year|fy)?\s*(20\d{2})\b", re.I),
    # Match "2024-25", "2023-24"
    re.compile(r"\b(20\d{2})[\-/]\d{2}\b"),
]


def _extract_year(question: str) -> Optional[str]:
    """
    Return a normalised year token from the question if present.
    E.g. 'FY2024', 'FY24', '2024' → 'FY24' or '2024'
    """
    # Try FY short form first
    m = re.search(r"\bfy\s*(?:20)?(\d{2})\b", question, re.I)
    if m:
        return f"FY{m.group(1)}"
    # Try 4-digit year
    m = re.search(r"\b(20\d{2})\b", question)
    if m:
        return m.group(1)
    return None


def _label_matches_year(label: str, target: str) -> bool:
    """
    Check if an Excel header label (e.g. 'Mar 2024', 'FY24', 'Mar-24')
    matches the target year token (e.g. 'FY24', '2024').
    """
    label_up  = label.upper().replace(" ", "").replace("-", "")
    target_up = target.upper().replace(" ", "")
    # FY24 vs FY24 or MAR2024 vs 2024
    if target_up in label_up:
        return True
    # FY24 → 2024 check: strip FY prefix and compare to last 2 digits of 4-digit year
    if target_up.startswith("FY"):
        short = target_up[2:]  # '24'
        return short in label_up
    return False


def _build_context_block(ctx: dict, target_year: Optional[str] = None) -> str:
    """
    Build a rich context block for the LLM.
    Renders a year-by-year financial table when year labels are available,
    otherwise falls back to single-period metrics.
    """
    fin = ctx.get("financials", {})
    af  = ctx.get("alpha_fields", {})
    cid = ctx.get("company_id", "Unknown")

    rev_s    = af.get("revenue_series",     [])
    ni_s     = af.get("npm_series",         [])  # these are ratios 0-1
    ebit_s   = af.get("ebit_margin_series", [])
    yr_labels = af.get("year_labels",       [])

    lines = [f"=== LIVE FINANCIAL DATA: {cid} (Sector: {af.get('sector','N/A')}) ==="]

    if fin.get("_data_quality", {}).get("incomplete"):
        lines.append("[Structured financials not available for this company. Answer based ONLY on the provided document excerpts below.]")
        lines.append("===")
        return "\n".join(lines)

    # ── Year-by-year table ────────────────────────────────────────────────────
    if yr_labels and rev_s and len(yr_labels) == len(rev_s):
        lines.append("")
        lines.append("Year-by-year P&L (INR Crore):")
        lines.append(f"{'Year':<12} {'Revenue':>12} {'Net Margin':>12} {'EBIT Margin':>12}")
        lines.append("-" * 52)
        for i, (lbl, rev) in enumerate(zip(yr_labels, rev_s)):
            npm  = round(ni_s[i]   * 100, 1) if i < len(ni_s)   else "-"
            ebtm = round(ebit_s[i] * 100, 1) if i < len(ebit_s) else "-"
            marker = " ◀ TARGET" if target_year and _label_matches_year(lbl, target_year) else ""
            lines.append(f"{lbl:<12} {rev:>12,.0f} {str(npm)+'%':>12} {str(ebtm)+'%':>12}{marker}")
        lines.append("")
    else:
        # Fallback: single period
        rev  = fin.get("revenue", 0)
        ni   = fin.get("net_income", 0)
        ebit = fin.get("ebit", 0)
        te   = max(fin.get("total_equity", 1), 1)
        debt = fin.get("total_debt", 0)
        cogs = fin.get("cogs", 0)
        net_m  = round(ni / rev * 100, 1)   if rev  else 0
        ebit_m = round(ebit / rev * 100, 1) if rev  else 0
        gm     = round((1 - cogs/rev)*100, 1) if rev and cogs else 0
        roe    = round(ni / te * 100, 1)    if te   else 0
        de     = round(debt / te, 2)        if te   else 0
        lines += [
            f"Revenue: INR {rev:,.0f} Cr | Net Income: INR {ni:,.0f} Cr",
            f"Net Margin: {net_m}% | EBIT Margin: {ebit_m}% | Gross Margin: {gm}%",
            f"ROE: {roe}% | D/E ratio: {de}x | Debt: INR {debt:,.0f} Cr",
        ]

    # ── Latest-period snapshot (always) ──────────────────────────────────────
    rev  = fin.get("revenue", 0)
    ni   = fin.get("net_income", 0)
    ebit = fin.get("ebit", 0)
    te   = max(fin.get("total_equity", 1), 1)
    debt = fin.get("total_debt", 0)
    de   = round(debt / te, 2) if te else 0
    roe  = round(ni / te * 100, 1) if te else 0

    latest_label = yr_labels[-1] if yr_labels else "Latest"
    lines += [
        f"Latest period ({latest_label}): Revenue INR {rev:,.0f} Cr | Net Income INR {ni:,.0f} Cr",
        f"ROE: {roe}% | Debt/Equity: {de}x | Sector: {af.get('sector','N/A')}",
    ]
    if target_year:
        lines.append(f"NOTE: User is asking about {target_year}. Use the ◀ TARGET row above for your primary answer.")
    lines.append("===")
    return "\n".join(lines)


_SYSTEM_PROMPT = """\
You are EREBUS, an elite AI research analyst specializing in Indian listed companies \
(NSE/BSE). You provide precise, data-driven answers with specific numbers, dates, and \
citations. Format your response clearly with relevant metrics. \
If live financial data is provided in the context block, use it as your primary source \
and prefer it over your training knowledge. Every claim should be traceable to a source or metric. \

STRICT RULES — never break these:
- DO NOT add any "Note:", "Disclaimer:", "Data Limitations:", or "Source:" footer sections.
- DO NOT mention training data cutoffs, knowledge cutoffs, or that data "may be speculative".
- DO NOT say phrases like "as my training data only goes up to", "I cannot verify", \
  "please refer to the company's official website", or "this is based on historical trends".
- If live financial data is provided above, treat it as current and authoritative — no caveats needed.
- If no live data is available, answer from your knowledge concisely without disclaimers.
- End your response with the financial analysis. No footnotes, no training data warnings.\
"""

_DISCLAIMER_BLOCK_RE = re.compile(
    r"\n?\*?\*?(?:Note|Disclaimer|Data Limitations?|Source|Caveat|Warning)\*?\*?:"
    r"[^\n]*(?:\n(?!\n)[^\n]*)*",
    re.IGNORECASE,
)

# Individual sentences that indicate training-data hedging
_HEDGE_SENTENCE_RE = re.compile(
    r"[^.!?\n]*(?:"
    r"training data only goes up to"
    r"|my knowledge (?:cutoff|is limited to)"
    r"|as of my (last )?(?:training|knowledge)"
    r"|based on (?:the company.s )?historical trends and industry averages"
    r"|please refer to the company.s official website"
    r"|this information is speculative"
    r"|the above information is speculative"
    r"|may not reflect the current"
    r"|subject to audit and may be revised"
    r")[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)


def _strip_disclaimers(text: str) -> str:
    """Remove LLM-generated disclaimer / training-cutoff blocks from the answer."""
    # Remove full Note:/Source:/Data Limitations: sections
    text = _DISCLAIMER_BLOCK_RE.sub("", text)
    # Remove individual hedge sentences
    text = _HEDGE_SENTENCE_RE.sub("", text)
    # Clean up excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()



class HistoryItem(BaseModel):
    role: str          # 'user' | 'assistant'
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    llm_provider: str = Field("openai", description="openai | anthropic | ollama | gemini")
    model: Optional[str] = Field(None, description="Override model name")
    company_id: Optional[str] = Field(None, description="Force a specific company context")
    history: list[HistoryItem] = Field(default=[], description="Prior turns, oldest first, max 6 items")


class SourceRef(BaseModel):
    label: str
    page: str
    chunk_text: Optional[str] = None
    file_key: Optional[str] = None
    type: str = "live_data"
    s3_key: Optional[str] = None   # Set for uploaded docs; None for live S3 financials


class ChatResponse(BaseModel):
    answer:        str
    sources:       list[SourceRef]
    company_id:    Optional[str]
    provider:      str
    model_used:    str
    context_loaded: bool
    chart_data:    Optional[dict] = None
    confidence:    Optional[float] = None      # 0-1 from verified pipeline
    gates_passed:  Optional[list]  = None      # which anti-hallucination gates passed
    failed_at:     Optional[str]   = None      # gate that caused "I don't know"


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse, summary="Freeform research chat")
async def chat(req: ChatRequest):
    """
    POST /chat  —  Optimized async pipeline

    Routing order (fastest first):
      1. FAQ intent   → static answer instantly (no LLM, no cache miss)
      2. Cache hit    → return cached result instantly
      3. DATA intent  → load company context + fast_pipeline (1 LLM call)
      4. GENERAL      → direct single LLM call
    """
    # ── Auto-detect provider from env (takes precedence) ─────────────────────
    _env_provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    provider = _env_provider if _env_provider else req.llm_provider

    valid_providers = ("openai", "anthropic", "ollama", "bedrock", "gemini", "groq")
    if provider not in valid_providers:
        raise HTTPException(400, detail=f"Invalid llm_provider: {provider}")


    # ── 0. Intent classification ──────────────────────────────────────────────
    from modules.cache.query_cache import classify_intent, get_cache, Intent
    intent, faq_answer = classify_intent(req.question)

    if intent == Intent.FAQ:
        logger.info("[chat] FAQ intent — static answer")
        return ChatResponse(
            answer         = faq_answer,
            sources        = [],
            company_id     = None,
            provider       = "static",
            model_used     = "static-kb",
            context_loaded = False,
            confidence     = 1.0,
            gates_passed   = ["faq"],
            failed_at      = None,
        )

    # ── 1. Check semantic cache ───────────────────────────────────────────────
    _cache = get_cache()
    cached = await _cache.get(req.question)
    if cached:
        logger.info("[chat] cache hit — returning instantly")
        return ChatResponse(**cached)

    # ── 2. Detect company + year ──────────────────────────────────────────────
    company_ids = _extract_companies(req.question)

    # For follow-ups
    if not company_ids and req.history:
        for item in reversed(req.history):
            found_hist = _extract_companies(item.content)
            if found_hist:
                company_ids = found_hist
                logger.info("[chat] Companies %s resolved from history", company_ids)
                break

    if not company_ids and req.company_id:
        company_ids = [req.company_id]
        
    primary_company_id = company_ids[0] if company_ids else None
    
    target_year = _extract_year(req.question)   # e.g. 'FY24', '2024', or None
    ctx_block   = ""
    sources: list[SourceRef] = []
    context_loaded = False
    chart_data: dict | None = None

    for cid in company_ids:
        try:
            ctx = load_company(cid)
            company_block = _build_context_block(ctx, target_year=target_year)
            
            if company_block.strip():
                if ctx_block:
                    ctx_block += "\n\n"
                ctx_block += f"=== {cid.upper()} FINANCIALS ===\n{company_block}"
                context_loaded = True
                
                # Assign chart_data to the first company loaded successfully
                if not chart_data:
                    chart_data = _build_chart_data(ctx)
                
                af          = ctx.get("alpha_fields", {})
                yr_labels   = af.get("year_labels", [])
                yr_range = f"{yr_labels[0]} – {yr_labels[-1]}" if yr_labels and yr_labels[0] != yr_labels[-1] else (yr_labels[0] if yr_labels else "Multi-year")
                _excel_keys = ctx.get("s3_files", {}).get("excel", [])
                _pdf_keys   = ctx.get("s3_files", {}).get("pdf",   [])
                _src_key    = _excel_keys[0] if _excel_keys else (_pdf_keys[0] if _pdf_keys else None)
                
                sources.append(SourceRef(
                    label  = f"{cid} · Live Financials (S3)",
                    page   = yr_range,
                    type   = "live_data",
                    s3_key = _src_key,
                ))
                logger.info("[chat] Loaded context for %s (years: %s, target_year: %s)",
                            cid, yr_range, target_year)
        except Exception as e:
            logger.warning("[chat] Could not load context for %s: %s", cid, e)

    # ── 3. Route: fast_pipeline (data) vs direct LLM (general) ──────────────
    # fast_pipeline does ONE structured LLM call instead of 4-6 sequential calls.
    answer       = None
    model_used   = "data-engine"
    confidence   = None
    gates_passed = None
    failed_at    = None

    trimmed_history = req.history[-6:] if req.history else []

    try:
        from modules.llm.generator        import get_generator, LLMProvider
        from modules.rag.fast_pipeline     import run_fast_rag

        provider_enum = LLMProvider(provider)
        gen           = get_generator(provider_enum)

        def _llm(prompt: str, max_tokens: int = 4096) -> str:
            try:
                r = gen.generate(
                    prompt        = prompt,
                    system_prompt = _SYSTEM_PROMPT,
                    model         = req.model,
                    temperature   = 0.2,
                    max_tokens    = max_tokens,
                    history       = [(h.role, h.content) for h in trimmed_history],
                )
                return r.text
            except Exception as _e:
                _estr = str(_e)
                # Auto-fallback to Gemini on Groq rate-limit
                if provider in ("groq",) and ("429" in _estr or "rate_limit" in _estr.lower() or "quota" in _estr.lower()):
                    logger.warning("[chat] Groq rate-limited — falling back to Gemini")
                    try:
                        _gem = get_generator(LLMProvider.GEMINI)
                        _r2  = _gem.generate(
                            prompt        = prompt,
                            system_prompt = _SYSTEM_PROMPT,
                            temperature   = 0.2,
                            max_tokens    = max_tokens,
                        )
                        return _r2.text
                    except Exception as _e2:
                        logger.error("[chat] Gemini fallback also failed: %s", _e2)
                raise  # re-raise the original if no fallback worked

        # FAISS retriever (non-fatal if unavailable)
        _retriever = None
        try:
            from modules.rag.query import RagRetriever
            _r = RagRetriever()
            # In FAISStore or vector_store, total_chunks isn't always directly accessible.
            # EREBUS vector_store returns count on .count() or .store
            # Instead of failing on .store check, we just inject it.
            _retriever = _r
        except Exception as _re:
            logger.debug("[chat] RAG retriever unavailable (non-fatal): %s", _re)

        if ctx_block.strip():
            # DATA path: grounded single-call pipeline
            fast = run_fast_rag(
                query             = req.question,
                llm_call          = _llm,
                retriever         = _retriever,
                company_filter    = primary_company_id,
                financial_context = ctx_block,
            )
            answer       = fast.answer
            confidence   = fast.confidence
            gates_passed = fast.gates_passed
            failed_at    = fast.failed_at

            for chunk_src in fast.sources:
                sources.append(SourceRef(
                    label  = chunk_src.get("label",  "Document"),
                    page   = chunk_src.get("page",   "?"),
                    chunk_text = chunk_src.get("chunk_text", ""),
                    file_key   = chunk_src.get("file_key"),
                    type   = chunk_src.get("type",   "rag_chunk"),
                    s3_key = chunk_src.get("s3_key", None),
                ))
        elif intent == Intent.DATA:
            # Explicit guard: Intended to ask about data, but no context loaded. 
            # Do NOT fallback to direct LLM to prevent severe hallucination.
            logger.warning("[chat] DATA intent aborted - context is empty")
            answer = "I don't have enough verified financial data loaded to answer this specific query. Please check if the company is supported."
            failed_at = "no_context"
        else:
            # GENERAL path: direct single LLM call
            logger.info("[chat] GENERAL intent — direct LLM")
            result = gen.generate(
                prompt        = req.question,
                system_prompt = _SYSTEM_PROMPT,
                model         = req.model,
                temperature   = 0.4,
                max_tokens    = 1200,
                history       = [(h.role, h.content) for h in trimmed_history],
            )
            answer = result.text

        # Recover model name
        try:
            _ping      = gen.generate("ping", system_prompt="", max_tokens=1)
            model_used = _ping.model
        except Exception:
            model_used = provider

    except Exception as llm_err:
        err_str  = str(llm_err)
        is_quota = (
            "429" in err_str or 
            "413" in err_str or 
            "RESOURCE_EXHAUSTED" in err_str or 
            "quota" in err_str.lower() or 
            "rate_limit_exceeded" in err_str.lower()
        )
        logger.warning("[chat] LLM unavailable (%s) — data-engine fallback", llm_err)

        if context_loaded and primary_company_id:
            try:
                ctx_fb     = load_company(primary_company_id)
                answer     = _build_data_answer(req.question, ctx_fb)
                model_used = "data-engine (quota)" if is_quota else "data-engine (no LLM key)"
            except Exception as e2:
                logger.error("[chat] fallback also failed: %s", e2)
                answer     = "I'm temporarily rate-limited. Please try again in a moment."
                model_used = "data-engine (error)"
        else:
            if is_quota:
                answer = (
                    "The AI model is temporarily rate-limited (quota or token limit exceeded). "
                    "Please wait a moment and try again. For companies with live financial data, "
                    "I can still provide data-engine summaries even when rate-limited."
                )
                model_used = "data-engine (quota)"
            else:
                answer = (
                    "No AI provider seems to be responding. If you are asking about a company "
                    "with live financial data (e.g., 'Analyse TCS'), I can still provide a "
                    "structured financial summary from the data engine."
                )
                model_used = "data-engine (unconfigured/error)"

    # ── 4. (Removed Auto-record in user_analytics) ───────────────────────────────
    # The frontend is now responsible for session state persistence using the 
    # POST /analytics and PUT /analytics endpoints.

    # ── 5. Sanitize answer — strip LLM disclaimer blocks ──────────────────────
    if answer:
        answer = _strip_disclaimers(answer)

    return ChatResponse(
        answer         = answer,
        sources        = sources,
        company_id     = primary_company_id,
        provider       = provider,
        model_used     = model_used,
        context_loaded = context_loaded,
        chart_data     = chart_data,
        confidence     = confidence,
        gates_passed   = gates_passed,
        failed_at      = failed_at,
    )




# ── Chart data builder ───────────────────────────────────────────────────────

def _build_chart_data(ctx: dict) -> dict:
    """
    Build structured chart data from company context for frontend visualizations.
    Returns:
        {
          company_id : str,
          sector     : str,
          revenue    : [{ year, revenue, net_income, ebit }],  # INR Crore
          margins    : [{ year, net, ebit, gm }],              # percentages
          ratios     : { roe, de, net_margin, ebit_margin, gross_margin,
                         interest_coverage, revenue_cr, net_income_cr }
        }
    """
    fin = ctx.get("financials", {})
    af  = ctx.get("alpha_fields", {})
    cid = ctx.get("company_id", "Unknown")

    yr_labels = af.get("year_labels", [])
    rev_s     = af.get("revenue_series",      [])   # INR Crore
    npm_s     = af.get("npm_series",          [])   # net profit margin 0–1
    ebit_s    = af.get("ebit_margin_series",  [])   # EBIT margin 0–1
    gm_s      = af.get("gross_margin_series", [])   # gross margin 0–1

    # ── Revenue + derived P&L series (combo chart) ────────────────────
    revenue = []
    for i, (lbl, rev) in enumerate(zip(yr_labels, rev_s)):
        if rev is None:
            continue
        entry = {"year": lbl, "revenue": round(rev, 0)}
        if i < len(npm_s) and npm_s[i] is not None:
            entry["net_income"] = round(rev * npm_s[i], 0)
        if i < len(ebit_s) and ebit_s[i] is not None:
            entry["ebit"] = round(rev * ebit_s[i], 0)
        revenue.append(entry)

    # ── Margin series (line chart) — % ────────────────────────────────
    margins = []
    for i, lbl in enumerate(yr_labels):
        entry = {"year": lbl}
        if i < len(npm_s)  and npm_s[i]  is not None: entry["net"]  = round(npm_s[i]  * 100, 1)
        if i < len(ebit_s) and ebit_s[i] is not None: entry["ebit"] = round(ebit_s[i] * 100, 1)
        if i < len(gm_s)   and gm_s[i]   is not None: entry["gm"]   = round(gm_s[i]   * 100, 1)
        margins.append(entry)

    # ── Snapshot ratios (latest financials) ───────────────────────────
    rev_l  = fin.get("revenue",           0) or 0
    ni_l   = fin.get("net_income",        0) or 0
    ebit_l = fin.get("ebit",              0) or 0
    debt   = fin.get("total_debt",        0) or 0
    eq     = fin.get("total_equity",      1) or 1
    cogs   = fin.get("cogs",              0) or 0
    int_e  = fin.get("interest_expense",  0) or 0

    ratios = {
        "roe":               round(ni_l  / eq     * 100, 1)      if eq              else None,
        "de":                round(debt  / eq,            2)      if eq              else None,
        "net_margin":        round(ni_l  / rev_l  * 100, 1)      if rev_l           else None,
        "ebit_margin":       round(ebit_l / rev_l * 100, 1)      if rev_l           else None,
        "gross_margin":      round((1 - cogs / rev_l) * 100, 1)  if rev_l and cogs  else None,
        "interest_coverage": round(ebit_l / int_e,       1)      if int_e           else None,
        "revenue_cr":        round(rev_l, 0),
        "net_income_cr":     round(ni_l,  0),
    }

    return {
        "company_id": cid,
        "sector":     af.get("sector", "N/A"),
        "revenue":    revenue,
        "margins":    margins,
        "ratios":     ratios,
    }



# ── Data-engine fallback ──────────────────────────────────────────────────────

def _build_data_answer(question: str, ctx: dict) -> str:
    """
    Build a structured, readable answer from live S3 financials —
    no LLM required. Extracts key metrics and formats them as a
    research-grade narrative.
    """
    fin = ctx.get("financials", {})
    af  = ctx.get("alpha_fields", {})
    cid = ctx.get("company_id", "Unknown")

    rev    = fin.get("revenue",     0) or 0
    ni     = fin.get("net_income",  0) or 0
    ebit   = fin.get("ebit",        0) or 0
    debt   = fin.get("total_debt",  0) or 0
    equity = fin.get("total_equity",1) or 1
    cogs   = fin.get("cogs",        0) or 0

    net_m  = round(ni   / rev * 100, 1) if rev else 0
    ebit_m = round(ebit / rev * 100, 1) if rev else 0
    gm     = round((1 - cogs / rev) * 100, 1) if rev and cogs else 0
    roe    = round(ni / equity * 100, 1) if equity else 0
    de     = round(debt / equity, 2)    if equity else 0

    rev_s = af.get("revenue_series", [])
    npm_s = af.get("npm_series", [])

    # Revenue trend narrative
    rev_trend = ""
    if len(rev_s) >= 2:
        cagr = round((rev_s[-1] / rev_s[0] - 1) * 100 / max(len(rev_s) - 1, 1), 1)
        direction = "grown" if cagr > 0 else "declined"
        rev_trend = (
            f"Revenue has {direction} at a CAGR of {abs(cagr)}% "
            f"over the last {len(rev_s)} periods, from INR {rev_s[0]:,.0f} Cr to INR {rev_s[-1]:,.0f} Cr."
        )

    margin_trend = ""
    if len(npm_s) >= 2:
        delta = round((npm_s[-1] - npm_s[0]) * 100, 1)
        direction = "expanded" if delta > 0 else "contracted"
        margin_trend = (
            f"Net margins have {direction} by {abs(delta)}pp from "
            f"{npm_s[0]*100:.1f}% to {npm_s[-1]*100:.1f}% over the same period."
        )

    risk_note = ""
    if de > 1.5:
        risk_note = f"Leverage is elevated with a Debt/Equity ratio of {de}x — a key risk factor."
    elif de < 0.2:
        risk_note = f"The balance sheet is virtually debt-free (D/E: {de}x), providing significant financial flexibility."

    sector = af.get("sector", "N/A")

    answer = (
        f"**{cid} - Financial Summary** (Live data from EREBUS)\n"
        f"*Sector: {sector}*\n\n"
        f"**Key Metrics (Latest Period)**\n"
        f"- Revenue: INR {rev:,.0f} Cr\n"
        f"- Net Income: INR {ni:,.0f} Cr\n"
        f"- EBIT: INR {ebit:,.0f} Cr\n"
        f"- Net Margin: {net_m}% | EBIT Margin: {ebit_m}% | Gross Margin: {gm}%\n"
        f"- Return on Equity: {roe}%\n"
        f"- Debt/Equity: {de}x\n\n"
        f"**Trend Analysis**\n"
        f"{rev_trend}\n"
        f"{margin_trend}\n"
        f"{risk_note}\n\n"
        f"**Context for your question:** \"{question}\"\n"
        f"Data sourced from {cid}'s filed financial statements in EREBUS S3 data store. "
        f"Enable Bedrock/OpenAI/Anthropic in .env for a full LLM-generated analysis."
    )

    return answer.strip()

