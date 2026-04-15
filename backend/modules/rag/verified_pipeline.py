"""
EREBUS · RAG · Verified Answer Pipeline
=========================================
Full anti-hallucination pipeline per the EREBUS design spec:

  Query
    ↓
  FAISS Retrieval (top 5)
    ↓
  Score Filter  (threshold 0.35 — cosine; FAISS returns inner-product on
                normalised vectors, so 1.0 = identical, 0.0 = orthogonal)
    ↓
  Answerability Check  (Groq single-call: YES / NO)
    ↓
  Context Compression  (top 3 chunks only)
    ↓
  Main LLM Answer      (Groq)
    ↓
  Verification Pass    (Groq: SUPPORTED / UNSUPPORTED)
    ↓
  Confidence Gate      (Groq: 0-1 float; < 0.6 → "I don't know")
    ↓
  Final Output
     { answer, confidence, sources, context_used, gates_passed }

IMPORTANT DESIGN RULES:
  - Less context  = less hallucination  (always clip to top 3)
  - If unsure     → return "I don't know" (never fabricate)
  - Verification  > generation
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Tuning knobs ──────────────────────────────────────────────────────────────
# Lowered from 0.75 (cosine on 1024-dim Titan vectors) to be more inclusive
# for financial text that is semantically related but not near-duplicate.
SCORE_THRESHOLD   = 0.35
CONFIDENCE_GATE   = 0.60
MAX_ANSWER_CHUNKS = 3   # CRITICAL: fewer chunks = fewer hallucinations
TOP_K_RETRIEVE    = 5


# ── Dataclass for the pipeline output ────────────────────────────────────────

class VerifiedAnswer:
    """Structured result from the verified RAG pipeline."""

    __slots__ = (
        "answer",
        "confidence",
        "sources",
        "context_used",
        "gates_passed",
        "failed_at",
    )

    def __init__(
        self,
        answer:       str,
        confidence:   float,
        sources:      List[Dict[str, Any]],
        context_used: bool,
        gates_passed: List[str],
        failed_at:    Optional[str] = None,
    ):
        self.answer       = answer
        self.confidence   = confidence
        self.sources      = sources
        self.context_used = context_used
        self.gates_passed = gates_passed
        self.failed_at    = failed_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer":       self.answer,
            "confidence":   self.confidence,
            "sources":      self.sources,
            "context_used": self.context_used,
            "gates_passed": self.gates_passed,
            "failed_at":    self.failed_at,
        }


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_verified_rag(
    query:          str,
    llm_call,                      # callable(prompt: str, max_tokens: int) → str
    retriever=None,                 # RagRetriever instance (optional)
    company_filter: Optional[str] = None,
    financial_context: str = "",    # pre-built context block from load_company()
) -> VerifiedAnswer:
    """
    Entry point.  Runs the full 6-stage anti-hallucination pipeline.

    Parameters
    ----------
    query            : The user's research question.
    llm_call         : Callable that accepts (prompt, max_tokens) and returns a string.
                       Uses Groq by default when called from the chat router.
    retriever        : Optional RagRetriever; if None, skips FAISS retrieval.
    company_filter   : Restrict FAISS results to one company.
    financial_context: Pre-built financial context block from load_company().
                       Used even if FAISS retrieval fails / is unavailable.

    Returns
    -------
    VerifiedAnswer
    """
    gates_passed: List[str] = []
    sources:      List[Dict[str, Any]] = []

    # ── Stage 1: Retrieval ────────────────────────────────────────────────────
    faiss_chunks: List[Dict[str, Any]] = []

    if retriever is not None:
        try:
            raw = retriever.retrieve_top_k(
                query,
                top_k=TOP_K_RETRIEVE,
                company_filter=company_filter,
            )
            # Filter mock stubs (similarity_score == 0.95 pattern is a dead giveaway)
            faiss_chunks = [c for c in raw if not _is_mock_stub(c)]
            logger.info("[rag-pipeline] Stage 1: retrieved %d chunks from FAISS", len(faiss_chunks))
        except Exception as e:
            logger.warning("[rag-pipeline] Stage 1 FAISS retrieval failed: %s", e)

    # ── Stage 2: Score filter ─────────────────────────────────────────────────
    filtered = [c for c in faiss_chunks if c.get("similarity_score", 0) >= SCORE_THRESHOLD]
    logger.info(
        "[rag-pipeline] Stage 2: score filter %s → %d passed (threshold=%.2f)",
        f"{len(faiss_chunks)}→{len(filtered)}", len(filtered), SCORE_THRESHOLD,
    )

    # ── Build context ─────────────────────────────────────────────────────────
    # Combine FAISS chunks (top 3) + the structured financial context block.
    # The structured context is ALWAYS included (it comes from the Excel data).
    chunk_texts: List[str] = [c.get("chunk_text", "") for c in filtered[:MAX_ANSWER_CHUNKS]]

    for c in filtered[:MAX_ANSWER_CHUNKS]:
        sources.append({
            "label":            c.get("doc_id", "S3 Document"),
            "page":             str(c.get("page", "?")),
            "type":             "rag_chunk",
            "similarity_score": round(c.get("similarity_score", 0), 3),
        })

    # Build final context:  structured financials FIRST, then PDF excerpts
    context_parts: List[str] = []
    if financial_context:
        context_parts.append(financial_context)
    if chunk_texts:
        context_parts.append("\n\n".join(chunk_texts))

    context = "\n\n---\n\n".join(context_parts)
    context_used = bool(context.strip())

    if not context_used:
        logger.warning("[rag-pipeline] No context available — returning I don't know")
        return VerifiedAnswer(
            answer       = "I don't have enough context to answer this question. Please ask about a company that has data loaded in EREBUS.",
            confidence   = 0.0,
            sources      = [],
            context_used = False,
            gates_passed = [],
            failed_at    = "no_context",
        )

    gates_passed.append("score_filter")

    # ── Stage 3: Answerability check ──────────────────────────────────────────
    can_answer = _check_answerability(query, context, llm_call)
    logger.info("[rag-pipeline] Stage 3: answerability = %s", can_answer)

    if not can_answer:
        return VerifiedAnswer(
            answer       = "I don't know. The available context doesn't contain enough information to answer this question reliably.",
            confidence   = 0.0,
            sources      = sources,
            context_used = True,
            gates_passed = gates_passed,
            failed_at    = "answerability_check",
        )

    gates_passed.append("answerability_check")

    # ── Stage 4: Main answer generation ──────────────────────────────────────
    answer = _generate_answer(query, context, llm_call)
    logger.info("[rag-pipeline] Stage 4: answer generated (%d chars)", len(answer))

    if not answer or _is_refusal(answer):
        return VerifiedAnswer(
            answer       = "I don't know.",
            confidence   = 0.0,
            sources      = sources,
            context_used = True,
            gates_passed = gates_passed,
            failed_at    = "generation_refusal",
        )

    gates_passed.append("answer_generated")

    # ── Stage 5: Verification pass ────────────────────────────────────────────
    is_supported = _verify_answer(answer, context, llm_call)
    logger.info("[rag-pipeline] Stage 5: verification = %s", is_supported)

    if not is_supported:
        return VerifiedAnswer(
            answer       = "I don't know. I generated an answer but could not verify it against the source data — this prevents me from sharing potentially incorrect information.",
            confidence   = 0.0,
            sources      = sources,
            context_used = True,
            gates_passed = gates_passed,
            failed_at    = "verification_failed",
        )

    gates_passed.append("verified")

    # ── Stage 6: Confidence gate ──────────────────────────────────────────────
    confidence = _get_confidence(answer, llm_call)
    logger.info("[rag-pipeline] Stage 6: confidence = %.2f (gate=%.2f)", confidence, CONFIDENCE_GATE)

    if confidence < CONFIDENCE_GATE:
        return VerifiedAnswer(
            answer       = f"I don't know with sufficient confidence (score: {confidence:.0%}). The data may be incomplete or the question may require information not in the loaded context.",
            confidence   = confidence,
            sources      = sources,
            context_used = True,
            gates_passed = gates_passed,
            failed_at    = "confidence_gate",
        )

    gates_passed.append("confidence_gate")

    return VerifiedAnswer(
        answer       = answer,
        confidence   = confidence,
        sources      = sources,
        context_used = True,
        gates_passed = gates_passed,
        failed_at    = None,
    )


# ── Stage implementations ─────────────────────────────────────────────────────

def _check_answerability(query: str, context: str, llm_call) -> bool:
    """Stage 3: Ask LLM if the context actually contains the answer. YES/NO only."""
    prompt = f"""You are a strict information checker.

CONTEXT (Financial Data):
{context[:3000]}

QUESTION:
{query}

Based ONLY on the context above, can this question be answered with specific facts or numbers?
Do NOT use your general knowledge.

Answer with ONLY one word: YES or NO"""

    try:
        result = llm_call(prompt, max_tokens=5)
        return "YES" in result.upper()
    except Exception as e:
        logger.warning("[rag-pipeline] Answerability check failed: %s — defaulting to YES", e)
        return True   # fail open: let the answer attempt happen


def _generate_answer(query: str, context: str, llm_call) -> str:
    """Stage 4: Generate the actual answer, grounded strictly in context."""
    prompt = f"""You are EREBUS, an elite financial analyst for Indian listed companies (NSE/BSE).

STRICT RULES:
1. Use ONLY the data in the CONTEXT block below. Do NOT use your general knowledge.
2. If any number is missing from the context, say "data not available".
3. If the answer is not in the context, say exactly: "I don't know"
4. Be precise: use exact numbers, percentages, and INR values from the context.

FORMAT YOUR RESPONSE AS CLEAN MARKDOWN:
- Start with a **bold one-line summary** (company name + key insight)
- Use bullet points for key metrics (Revenue, Net Income, Margins, ROE, D/E)
- End with 1–2 sentences on the trend or key takeaway
- Use **bold** for numbers and metric names
- Keep total response under 150 words

CONTEXT:
{context[:4000]}

QUESTION:
{query}

ANSWER:"""

    try:
        return llm_call(prompt, max_tokens=400).strip()
    except Exception as e:
        logger.error("[rag-pipeline] Answer generation failed: %s", e)
        return ""



def _verify_answer(answer: str, context: str, llm_call) -> bool:
    """Stage 5: Chain-of-Verification light — check answer is grounded in context."""
    prompt = f"""You are a strict fact-checker for financial data.

CONTEXT (the ONLY allowed source):
{context[:3000]}

GENERATED ANSWER:
{answer}

Is every specific claim, number, and percentage in the ANSWER directly supported by the CONTEXT?
Do NOT accept answers that use general knowledge not in the context.

Answer with ONLY one word: SUPPORTED or UNSUPPORTED"""

    try:
        result = llm_call(prompt, max_tokens=10)
        return "SUPPORTED" in result.upper()
    except Exception as e:
        logger.warning("[rag-pipeline] Verification failed: %s — defaulting to UNSUPPORTED", e)
        return False   # fail closed: safety first


def _get_confidence(answer: str, llm_call) -> float:
    """Stage 6: Ask LLM to self-score confidence in the answer (0.0–1.0)."""
    prompt = f"""Rate the confidence level of this financial analysis answer.

ANSWER:
{answer}

Consider:
- Are specific numbers cited? (higher confidence)
- Are there hedging words like "approximately", "unclear", "might"? (lower confidence)
- Is the answer complete or does it say "data not available"? (lower confidence)

Reply with ONLY a decimal number between 0.0 and 1.0.
Example: 0.85"""

    try:
        result = llm_call(prompt, max_tokens=8).strip()
        # Extract first float found in the response
        match = re.search(r"(\d+(?:\.\d+)?)", result)
        if match:
            val = float(match.group(1))
            # Normalise: if someone returns "85" instead of "0.85"
            if val > 1.0:
                val = val / 100.0
            return round(min(max(val, 0.0), 1.0), 2)
    except Exception as e:
        logger.warning("[rag-pipeline] Confidence scoring failed: %s — defaulting to 0.5", e)
    return 0.5


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_mock_stub(chunk: Dict[str, Any]) -> bool:
    """Detect mock stub chunks returned when FAISS index is empty."""
    text = chunk.get("chunk_text", "")
    return "[MOCK CHUNK" in text


def _is_refusal(text: str) -> bool:
    """Check if the LLM explicitly said it doesn't know."""
    lowered = text.lower().strip()
    return (
        lowered.startswith("i don't know")
        or lowered.startswith("i do not know")
        or lowered == "i don't know."
    )
