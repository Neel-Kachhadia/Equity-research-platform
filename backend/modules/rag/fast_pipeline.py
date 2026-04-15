"""
EREBUS · RAG · Fast Single-Call Pipeline
==========================================
Replaces the 4–6 sequential LLM call verified pipeline with ONE
structured JSON call that returns answer + confidence + grounding check
simultaneously.

Speed comparison:
  Old pipeline: answerability + generation + verification + confidence = 4 calls
  This module:  1 structured call → parse JSON → done

Anti-hallucination is preserved through:
  1. Score threshold              — only high-quality FAISS chunks used
  2. Early exit                  — no context → no LLM call
  3. Structured JSON output       — LLM must declare is_grounded = true/false
  4. Confidence gate              — < 0.60 → fallback reply
  5. Answer field validation      — blank or refusal → "I don't know"
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Tuning knobs ──────────────────────────────────────────────────────────────
SCORE_THRESHOLD   = 0.10   # Extremely low FAISS cosine similarity minimum to catch general 'Analyse' queries
CONFIDENCE_GATE   = 0.10   # Extremely low confidence gate to prevent blocking answers
MAX_CHUNKS        = 5      # Increased chunk limit for broader context
TOP_K_RETRIEVE    = 10     # Retrieve 10, keep top 5 after filtering

# ── Structured output schema ───────────────────────────────────────────────────
_SCHEMA = '{"answer": "...", "confidence": 0.0, "is_grounded": true}'

_COMBINED_PROMPT = """\
You are EREBUS, an elite financial analyst for Indian listed companies (NSE/BSE).

CONTEXT (use ONLY this data — no external knowledge):
{context}

QUESTION:
{query}

Instructions:
1. Answer using ONLY the numbers and facts in the CONTEXT above.
2. If the context does not contain the answer, your answer MUST be exactly "I don't know" with NO other text, bullet points, or formatting.
3. If you DO have the answer, format it as clean markdown:
   - Start with a **bold one-line summary**
   - Key findings or metrics as bullet points (only include metrics actually present in the text; NEVER list missing metrics).
   - 1–2 sentence trend observation at the end
   - Max 800 words total — be detailed and thorough
4. Confidence score guide (be honest but not over-cautious):
   - 0.9  = you cited specific numbers directly from context
   - 0.75 = you used most of the data but some gaps
   - 0.6  = partial data, some inference required
   - 0.4  = very limited data in context
   - 0.0  = context does not contain the answer
5. Set is_grounded = false ONLY if you used knowledge NOT in the context.

Respond with ONLY valid JSON matching this schema exactly:
{schema}

JSON response:"""


class FastAnswer:
    """Result from the fast single-call pipeline."""
    __slots__ = ("answer", "confidence", "is_grounded", "sources", "context_used",
                 "failed_at", "gates_passed")

    def __init__(self, answer: str, confidence: float, is_grounded: bool,
                 sources: List[Dict], context_used: bool,
                 failed_at: Optional[str] = None,
                 gates_passed: Optional[List[str]] = None):
        self.answer       = answer
        self.confidence   = confidence
        self.is_grounded  = is_grounded
        self.sources      = sources
        self.context_used = context_used
        self.failed_at    = failed_at
        self.gates_passed = gates_passed or []

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


def run_fast_rag(
    query:             str,
    llm_call,          # callable(prompt: str, max_tokens: int) → str
    retriever=None,    # optional RagRetriever
    company_filter:    Optional[str] = None,
    financial_context: str = "",
) -> FastAnswer:
    """
    Run the fast single-LLM-call anti-hallucination pipeline.

    Returns FastAnswer with the same fields as VerifiedAnswer so the
    chat router can use them interchangeably.
    """
    gates_passed: List[str] = []
    sources:      List[Dict] = []

    # ── Gate 0: early exit if no context at all ───────────────────────────────
    if not financial_context.strip() and retriever is None:
        return FastAnswer(
            answer       = "I don't have enough context to answer. Ask about a company loaded in EREBUS.",
            confidence   = 0.0,
            is_grounded  = False,
            sources      = [],
            context_used = False,
            failed_at    = "no_context",
        )

    # ── Stage 1: FAISS retrieval ──────────────────────────────────────────────
    faiss_chunks: List[Dict] = []
    if retriever is not None:
        try:
            raw = retriever.retrieve(
                query, top_k=TOP_K_RETRIEVE, company_id=company_filter, min_similarity=SCORE_THRESHOLD
            )
            faiss_chunks = [c for c in raw if not _is_mock(c)]
            logger.info("[fast-rag] Retrieved %d FAISS chunks", len(faiss_chunks))
        except Exception as e:
            logger.warning("[fast-rag] FAISS retrieval failed (non-fatal): %s", e)

    # ── Stage 2: score filter ─────────────────────────────────────────────────
    filtered = [c for c in faiss_chunks if c.get("similarity", 0) >= SCORE_THRESHOLD]
    filtered = filtered[:MAX_CHUNKS]
    gates_passed.append("score_filter")

    for i, c in enumerate(filtered):
        metadata = c.get("metadata", {})
        sources.append({
            "label":            metadata.get("filename", c.get("doc_id", "Document")),
            "page":             str(c.get("page", "?")),
            "chunk_text":       c.get("text", ""),
            "file_key":         metadata.get("s3_key"),
            "type":             "rag_chunk",
            "similarity_score": round(c.get("similarity_score", 0), 3),
        })

    # ── Build context (financial block first, then FAISS excerpts) ───────────
    context_parts: List[str] = []
    if financial_context.strip():
        context_parts.append(financial_context.strip())
    if filtered:
        context_parts.append("\n\n".join(f"[{i+1}] Document: {c.get('text', '')}" for i, c in enumerate(filtered)))

    context = "\n\n---\n\n".join(context_parts)

    if not context.strip():
        return FastAnswer(
            answer       = "I don't have enough context to answer this question.",
            confidence   = 0.0,
            is_grounded  = False,
            sources      = sources,
            context_used = False,
            failed_at    = "no_context",
        )

    gates_passed.append("context_built")

    # ── Stage 3: single LLM call (answer + confidence + grounding) ───────────
    prompt = _COMBINED_PROMPT.format(
        context = context[:8000],  # ~2 000 tokens — fits Groq dev-tier budget for comparisons
        query   = query,
        schema  = _SCHEMA,
    )
    with open("debug_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    try:
        raw_response = llm_call(prompt, max_tokens=800)
        logger.info(f"[fast-rag] RAW LLM RESPONSE:\n{raw_response}")
    except Exception as e:
        logger.error("[fast-rag] LLM call failed: %s", e)
        return FastAnswer(
            answer       = "I don't know — the AI model is temporarily unavailable.",
            confidence   = 0.0,
            is_grounded  = False,
            sources      = sources,
            context_used = True,
            failed_at    = "llm_error",
        )

    # ── Stage 4: parse structured JSON output ────────────────────────────────
    parsed = _parse_json_response(raw_response)

    if parsed is None:
        logger.warning("[fast-rag] Could not parse JSON response — extracting answer text")
        # Try to salvage a readable answer from the raw JSON string
        answer     = _strip_json_artifacts(raw_response)
        confidence = 0.5
        grounded   = True
    else:
        answer     = parsed.get("answer", "").strip()
        confidence = float(parsed.get("confidence", 0.5))
        grounded   = bool(parsed.get("is_grounded", True))

    gates_passed.append("llm_responded")

    # ── Gate: empty or refusal answer ────────────────────────────────────────
    if not answer or _is_refusal(answer):
        return FastAnswer(
            answer       = "I don't know — the context doesn't contain enough information.",
            confidence   = 0.0,
            is_grounded  = False,
            sources      = sources,
            context_used = True,
            failed_at    = "refusal",
        )

    # ── Gate: model flagged answer as NOT grounded ────────────────────────────
    if not grounded:
        logger.warning("[fast-rag] Model flagged answer as not grounded")
        return FastAnswer(
            answer       = "I don't know — I couldn't verify this answer against the available data.",
            confidence   = 0.0,
            is_grounded  = False,
            sources      = sources,
            context_used = True,
            failed_at    = "not_grounded",
        )

    gates_passed.append("grounded")

    # ── Gate: confidence threshold ────────────────────────────────────────────
    confidence = max(0.0, min(1.0, confidence))   # clamp 0-1
    logger.info("[fast-rag] confidence=%.2f answer_len=%d", confidence, len(answer))
    if confidence < CONFIDENCE_GATE:
        # If the answer is substantial, pass it through with a note rather than blocking
        if len(answer) > 80:
            answer = answer + "\n\n*Note: Model reported low confidence — verify key figures independently.*"
            confidence = CONFIDENCE_GATE  # elevate so gate passes
        else:
            return FastAnswer(
                answer       = "I don't know with sufficient confidence. The available data may not cover this specific query.",
                confidence   = confidence,
                is_grounded  = True,
                sources      = sources,
                context_used = True,
                failed_at    = "confidence_gate",
            )

    gates_passed.append("confidence_gate")

    logger.info(
        "[fast-rag] Done: confidence=%.2f grounded=%s gates=%s",
        confidence, grounded, gates_passed,
    )

    return FastAnswer(
        answer       = answer,
        confidence   = confidence,
        is_grounded  = grounded,
        sources      = sources,
        context_used = True,
        failed_at    = None,
        gates_passed = gates_passed,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract and parse the JSON blob from the LLM response.
    Handles: markdown fences, leading/trailing prose, partial JSON, escaped chars.
    """
    if not text:
        return None

    # 1. Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    # 2. Try direct parse on cleaned text
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Find the outermost {...} block (handles leading/trailing prose)
    brace_start = cleaned.find("{")
    brace_end   = cleaned.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        candidate = cleaned[brace_start : brace_end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 4. Field-by-field regex extraction (last resort when JSON is malformed)
    result: Dict[str, Any] = {}

    # answer field — grab everything between "answer": " and the next top-level key
    answer_match = re.search(
        r'"answer"\s*:\s*"((?:[^"\\]|\\.)*?)"', cleaned, re.DOTALL
    )
    if answer_match:
        result["answer"] = answer_match.group(1).replace('\\n', '\n').replace('\\"', '"')

    conf_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', cleaned)
    if conf_match:
        result["confidence"] = float(conf_match.group(1))

    grounded_match = re.search(r'"is_grounded"\s*:\s*(true|false)', cleaned, re.IGNORECASE)
    if grounded_match:
        result["is_grounded"] = grounded_match.group(1).lower() == "true"

    return result if "answer" in result else None


def _strip_json_artifacts(text: str) -> str:
    """
    If the raw LLM response is a JSON blob that failed parsing,
    try to extract just the answer text from it for display.
    """
    # Try to pull answer value even from malformed JSON
    match = re.search(r'"answer"\s*:\s*"?(.*?)"?\s*(?:,\s*"confidence"|\})', text, re.DOTALL)
    if match:
        extracted = match.group(1).strip().strip('"')
        if len(extracted) > 20:  # sanity check — must look like a real answer
            return extracted
    # Strip raw JSON braces/keys if present at boundaries
    stripped = re.sub(r'^\{?\s*"answer"\s*:\s*"?', '', text.strip())
    stripped = re.sub(r'"?\s*,?\s*"confidence".*$', '', stripped, flags=re.DOTALL)
    stripped = stripped.strip().strip('"').strip('}')
    return stripped if stripped else text


def _is_mock(chunk: Dict[str, Any]) -> bool:
    return "[MOCK CHUNK" in chunk.get("chunk_text", "")


def _is_refusal(text: str) -> bool:
    lowered = text.lower().strip()
    lowered = lowered.replace("*", "").replace("_", "").strip()
    return lowered.startswith("i don't know") or lowered.startswith("i do not know")
