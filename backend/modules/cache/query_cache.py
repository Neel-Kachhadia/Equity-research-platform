"""
EREBUS · Query Cache — Semantic In-Memory Cache
=================================================
Two-layer cache:
  1. Exact match   — O(1) dict lookup, normalised key
  2. Semantic match — cosine similarity on sentence embeddings
                      (only if sentence-transformers available;
                       degrades gracefully without it)

Intent Router:
  Classifies queries before hitting LLM:
    FAQ     → predefined answers (no LLM, no cache miss)
    data    → FAISS + fast_pipeline
    general → direct LLM call

Thread-safe for async FastAPI usage (asyncio.Lock).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
CACHE_MAX_SIZE      = 200          # max cached queries
CACHE_TTL_SECONDS   = 3600        # 1 hour TTL
SEMANTIC_THRESHOLD  = 0.82        # cosine similarity to count as "same query"
SEMANTIC_ENABLED    = True        # set False to disable embedding-based lookup


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: In-memory semantic cache
# ══════════════════════════════════════════════════════════════════════════════

class QueryCache:
    """
    Thread-safe semantic cache with exact + semantic lookup.

    Usage:
        cache = QueryCache()
        hit = cache.get(query)
        if hit: return hit
        ...compute result...
        cache.put(query, result)
    """

    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: int = CACHE_TTL_SECONDS):
        self._exact: OrderedDict[str, Tuple[Dict, float]] = OrderedDict()  # key → (result, ts)
        self._semantic_entries: List[Tuple[Any, str, float]] = []          # (embedding, key, ts)
        self._max_size = max_size
        self._ttl      = ttl
        self._lock     = asyncio.Lock()
        self._embedder = None   # lazy-loaded sentence-transformers model
        self.hits_exact    = 0
        self.hits_semantic = 0
        self.misses        = 0

    # ── Public API ────────────────────────────────────────────────────────────

    async def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Return cached result or None."""
        async with self._lock:
            self._evict_expired()
            key = _normalise(query)

            # Layer 1: exact match
            if key in self._exact:
                result, _ = self._exact[key]
                self._exact.move_to_end(key)
                self.hits_exact += 1
                logger.debug("[cache] exact hit for '%s'", query[:40])
                return result

            # Layer 2: semantic match (if embedder available)
            if SEMANTIC_ENABLED and self._semantic_entries:
                emb = await self._embed(query)
                if emb is not None:
                    best_score, best_key = self._best_semantic(emb)
                    if best_score >= SEMANTIC_THRESHOLD and best_key in self._exact:
                        result, _ = self._exact[best_key]
                        self.hits_semantic += 1
                        logger.debug(
                            "[cache] semantic hit (%.3f) for '%s'", best_score, query[:40]
                        )
                        return result

            self.misses += 1
            return None

    async def put(self, query: str, result: Dict[str, Any]) -> None:
        """Store a result. Evicts LRU when full."""
        async with self._lock:
            key = _normalise(query)
            ts  = time.time()

            # Evict if full
            if len(self._exact) >= self._max_size:
                self._exact.popitem(last=False)

            self._exact[key] = (result, ts)
            self._exact.move_to_end(key)

            # Store embedding for semantic lookup
            if SEMANTIC_ENABLED:
                emb = await self._embed(query)
                if emb is not None:
                    self._semantic_entries.append((emb, key, ts))
                    # Trim to max_size
                    if len(self._semantic_entries) > self._max_size:
                        self._semantic_entries.pop(0)

    def stats(self) -> Dict[str, int]:
        return {
            "cached":         len(self._exact),
            "hits_exact":     self.hits_exact,
            "hits_semantic":  self.hits_semantic,
            "misses":         self.misses,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _evict_expired(self) -> None:
        """Remove entries older than TTL."""
        now    = time.time()
        cutoff = now - self._ttl
        stale  = [k for k, (_, ts) in self._exact.items() if ts < cutoff]
        for k in stale:
            del self._exact[k]
        self._semantic_entries = [(e, k, ts) for e, k, ts in self._semantic_entries
                                  if ts >= cutoff]

    async def _embed(self, text: str):
        """Lazy-load sentence-transformers and embed the query."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("[cache] sentence-transformers model loaded")
            except ImportError:
                logger.info("[cache] sentence-transformers not installed — semantic cache disabled")
                return None
            except Exception as e:
                logger.warning("[cache] embedder load failed: %s", e)
                return None
        try:
            vec = self._embedder.encode(text, normalize_embeddings=True)
            return vec
        except Exception:
            return None

    def _best_semantic(self, query_emb) -> Tuple[float, str]:
        """Return (best_score, cache_key) against stored embeddings."""
        import numpy as np
        best_score = -1.0
        best_key   = ""
        q = np.array(query_emb, dtype=np.float32)
        for stored_emb, key, _ in self._semantic_entries:
            score = float(np.dot(q, np.array(stored_emb, dtype=np.float32)))
            if score > best_score:
                best_score = score
                best_key   = key
        return best_score, best_key


# Singleton — shared across all requests
_query_cache = QueryCache()

def get_cache() -> QueryCache:
    return _query_cache


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Intent router
# ══════════════════════════════════════════════════════════════════════════════

class Intent:
    FAQ     = "faq"      # answer from static KB, no LLM
    DATA    = "data"     # company-specific → fast_pipeline
    GENERAL = "general"  # general financial Q → direct LLM
    UNKNOWN = "unknown"  # fallback → direct LLM


# ── Static FAQ knowledge base ──────────────────────────────────────────────────
_FAQ_KB: Dict[str, str] = {
    "what is erebus": (
        "**EREBUS** is an AI-powered financial research platform for Indian listed companies (NSE/BSE). "
        "It ingests company filings and Screener.in data from S3, runs quantitative analysis, "
        "and answers research questions using a verified RAG pipeline."
    ),
    "what is rag": (
        "**RAG (Retrieval-Augmented Generation)** is a technique that grounds LLM answers in "
        "retrieved document chunks, reducing hallucinations by only using facts present in the source data."
    ),
    "what is nse": (
        "**NSE (National Stock Exchange)** is India's largest stock exchange by trading volume, "
        "headquartered in Mumbai. It introduced the NIFTY 50 index."
    ),
    "what is bse": (
        "**BSE (Bombay Stock Exchange)** is Asia's oldest stock exchange, established in 1875, "
        "headquartered in Mumbai. It publishes the SENSEX index."
    ),
    "what is p/e ratio": (
        "**P/E (Price-to-Earnings) ratio** = Stock Price ÷ EPS. It measures how much investors "
        "pay per rupee of earnings. A high P/E implies growth expectations; a low P/E may indicate "
        "undervaluation or slower growth."
    ),
    "what is roe": (
        "**ROE (Return on Equity)** = Net Income ÷ Shareholders Equity × 100. "
        "It measures how efficiently a company uses equity to generate profit. "
        "ROE > 20% is generally considered strong for Indian IT companies."
    ),
    "what is ebitda": (
        "**EBITDA** = Earnings Before Interest, Taxes, Depreciation & Amortisation. "
        "It is a proxy for operating cash flow and is commonly used for valuation multiples."
    ),
    "hello": "Hello! I'm EREBUS, your AI financial analyst for Indian markets. Ask me about any NSE/BSE listed company.",
    "hi": "Hi! Ask me about any Indian listed company — TCS, Infosys, Reliance, HDFC Bank, and more.",
}

# ── Patterns that strongly indicate company data queries ──────────────────────
_DATA_PATTERNS = [
    r"\b(revenue|profit|margin|roe|ebit|roce|eps|pe ratio|debt|equity|cagr|npm|gross margin)\b",
    r"\b(analyse|analyze|analysis|financials|performance|results|quarterly|annual|fy\d{2})\b",
    r"\b(compare|vs|versus|against|better|worse)\b.*\b(tcs|infosys|wipro|reliance|hdfc|sbi|icici)\b",
    r"\b(tcs|infosys|wipro|hcl|techm|reliance|hdfc|icici|sbi|axis|kotak|asian paints|titan|bajaj)\b",
]
_DATA_RE = re.compile("|".join(_DATA_PATTERNS), re.IGNORECASE)

_FAQ_STOPWORDS = {"is", "a", "an", "the", "what", "?"}


def classify_intent(query: str) -> Tuple[str, Optional[str]]:
    """
    Returns (intent, faq_answer_or_None).

    Fast O(1) for FAQ, O(n_patterns) for data detection.
    """
    q_lower = query.lower().strip().rstrip("?").strip()

    # ── FAQ lookup (normalised exact match) ───────────────────────────────────
    for faq_key, faq_answer in _FAQ_KB.items():
        if re.search(r'\b' + re.escape(faq_key) + r'\b', q_lower):
            return Intent.FAQ, faq_answer

    # ── Data intent (company or financial keyword present) ────────────────────
    if _DATA_RE.search(query):
        return Intent.DATA, None

    # ── Default: general financial question → direct LLM ─────────────────────
    return Intent.GENERAL, None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Deterministic cache key: lowercase, strip punctuation, collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text
