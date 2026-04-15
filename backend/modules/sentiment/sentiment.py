"""
EREBUS · Module 4 — Sentiment Analysis (NLP Signal)
=====================================================
Extracts tone and sentiment signals from earnings call transcripts
and MD&A sections using FinBERT (ProsusAI/finbert).

Architecture §M4 outputs:
  - Per-sentence classification: Positive / Negative / Neutral
  - Aggregated sentiment score per period  [0, 1]
  - Sentiment trajectory signal (improving / stable / deteriorating)
  - Hedge language ratio (uncertainty / qualifications detected)

TWO-TIER IMPLEMENTATION:
  Tier 1 (Primary):   FinBERT via HuggingFace `transformers` + `torch`
  Tier 2 (Fallback):  Rule-based Financial Lexicon scorer
                      → activates automatically if torch/transformers not installed
                      → keeps module importable without ML stack

DEPENDENCIES (optional but strongly recommended for production):
  pip install torch transformers

Usage:
    from modules.sentiment.sentiment import SentimentAnalyser

    analyser = SentimentAnalyser()
    result = analyser.analyse_document("Revenue grew 18%... margins remain under pressure...")
    print(result["sentiment_score"])    # float [0, 1]
    print(result["pos_ratio"])         # fraction of positive sentences
    print(result["trajectory"])        # "improving" | "stable" | "deteriorating"
"""

from __future__ import annotations

import re
import logging
import statistics
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# ── FinBERT availability check ─────────────────────────────────────────────────
try:
    from transformers import pipeline as hf_pipeline
    import torch
    _FINBERT_AVAILABLE = True
    logger.info("FinBERT (transformers + torch) detected — using neural sentiment pipeline.")
except ImportError:
    _FINBERT_AVAILABLE = False
    logger.warning(
        "transformers/torch not installed. Falling back to rule-based lexicon scorer. "
        "Install with: pip install torch transformers"
    )


# ── Financial Sentiment Lexicon (Fallback) ────────────────────────────────────
# Curated financial domain word lists for the rule-based fallback tier.

_POSITIVE_WORDS = {
    "growth", "grew", "increase", "increased", "strong", "strength",
    "record", "robust", "expand", "expanded", "expansion", "outperform",
    "beat", "exceeded", "ahead", "profit", "profitable", "profitability",
    "improve", "improved", "improvement", "gain", "gains", "positive",
    "confidence", "confident", "momentum", "accelerate", "recovery",
    "resilient", "solid", "healthy", "optimistic", "upside", "opportunity",
    "win", "won", "deliver", "delivered", "milestone", "breakthrough",
    "efficiency", "margin", "earnings", "dividend", "shareholder",
}

_NEGATIVE_WORDS = {
    "decline", "declined", "decrease", "fell", "fall", "weak", "weakness",
    "loss", "losses", "pressure", "pressures", "headwind", "headwinds",
    "challenging", "challenge", "challenges", "difficult", "difficulty",
    "concern", "concerns", "risk", "risks", "uncertain", "uncertainty",
    "slowdown", "contraction", "deteriorate", "deteriorated", "miss",
    "missed", "below", "disappoint", "disappointing", "impairment",
    "write-off", "writedown", "layoff", "restructure", "restructuring",
    "inflation", "volatile", "volatility", "disruption", "disrupted",
}

# Both single words AND multi-word phrases — matched against lowercased full text
_HEDGE_WORDS = [
    # Single-word hedges
    "may", "might", "could", "should", "would", "possibly",
    "potentially", "approximately", "roughly", "around", "nearly",
    "assuming", "expect", "expected", "anticipate", "believe",
    "estimate", "project", "target", "guidance", "outlook", "forecast",
    "contingent", "conditional", "uncertain", "while", "although",
    "however", "nevertheless", "notwithstanding",
    # Multi-word phrases (critical for catching real hedging)
    "subject to", "depending on", "subject to approval",
    "we expect to", "we believe", "we anticipate",
    "subject to market", "if conditions", "assuming continued",
    "may be impacted", "could be affected",
]


# ── Sentence Splitter ──────────────────────────────────────────────────────────

def split_sentences(text: str) -> List[str]:
    """
    Split financial text into sentences. Protects known abbreviations
    like 'Rs.', 'FY24.', 'Q3.' from being treated as sentence endings.
    """
    # Replace known abbreviation dots with a placeholder
    _ABBREV = [
        'Rs', 'Mr', 'Ms', 'Mrs', 'Dr', 'vs', 'etc',
        'No', 'Co', 'Ltd', 'Inc', 'Corp', 'approx',
        # Fiscal/quarter patterns handled below via regex
    ]
    protected = text
    for abbr in _ABBREV:
        protected = protected.replace(abbr + '.', abbr + '<<DOT>>')

    # Protect FY24., Q3., H1. patterns
    protected = re.sub(r'\b(FY|Q[1-4]|H[12])\d{2,4}\.', lambda m: m.group().replace('.', '<<DOT>>'), protected)

    # Split on '. ', '! ', '? ' followed by uppercase or digit
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\(\d])', protected)

    # Restore placeholders and clean up
    sentences = [s.replace('<<DOT>>', '.').strip() for s in sentences if s.strip()]

    # Filter very short fragments
    return [s for s in sentences if len(s.split()) >= 4]


# ── Rule-Based Scorer (Tier 2 Fallback) ──────────────────────────────────────

def _lexicon_score_sentence(sentence: str) -> str:
    """
    Classify a single sentence as 'positive', 'negative', or 'neutral'.
    Uses regex tokenization to handle punctuation correctly.
    Fix: re.findall avoids 'growth.' != 'growth' mismatches.
    """
    words = set(re.findall(r'\b\w+\b', sentence.lower()))
    pos_hits = len(words & _POSITIVE_WORDS)
    neg_hits = len(words & _NEGATIVE_WORDS)

    if pos_hits > neg_hits:
        return "positive"
    elif neg_hits > pos_hits:
        return "negative"
    return "neutral"


def _lexicon_analyse(sentences: List[str]) -> List[Dict[str, Any]]:
    """Run rule-based classification on a list of sentences."""
    results = []
    for sent in sentences:
        label = _lexicon_score_sentence(sent)
        # Map label → probability-style scores for uniform downstream API
        if label == "positive":
            scores = {"positive": 0.75, "negative": 0.10, "neutral": 0.15}
        elif label == "negative":
            scores = {"positive": 0.10, "negative": 0.75, "neutral": 0.15}
        else:
            scores = {"positive": 0.20, "negative": 0.20, "neutral": 0.60}
        results.append({"sentence": sent, "label": label, "scores": scores})
    return results


# ── FinBERT Scorer (Tier 1 Primary) ──────────────────────────────────────────

_finbert_pipe = None  # singleton — loaded lazily on first call

def _get_finbert_pipe():
    global _finbert_pipe
    if _finbert_pipe is None:
        logger.info("Loading FinBERT model (ProsusAI/finbert)... this may take 30–60s on first run.")
        _finbert_pipe = hf_pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            top_k=None,                     # return all class scores
            truncation=True,
            max_length=512,
            device=-1,                      # CPU; set device=0 for GPU
        )
        logger.info("FinBERT model loaded successfully.")
    return _finbert_pipe


def _finbert_analyse(sentences: List[str], batch_size: int = 16) -> List[Dict[str, Any]]:
    """
    Run FinBERT inference in batches. Returns per-sentence label + scores.
    """
    pipe = _get_finbert_pipe()
    results = []

    for i in range(0, len(sentences), batch_size):
        batch = sentences[i: i + batch_size]
        # Only truncate sentences that genuinely exceed FinBERT's token limit
        # Cutting to 1500 chars is safer than a hard 1024 which may split mid-word
        FINBERT_CHAR_LIMIT = 1500
        batch_trimmed = [
            s[:FINBERT_CHAR_LIMIT] if len(s) > FINBERT_CHAR_LIMIT else s
            for s in batch
        ]

        try:
            raw_outputs = pipe(batch_trimmed)
        except Exception as e:
            logger.error(f"FinBERT batch inference failed: {e}. Using lexicon for this batch.")
            results.extend(_lexicon_analyse(batch))
            continue

        for sent, output in zip(batch, raw_outputs):
            # output is list of {"label": str, "score": float}
            score_map = {item["label"].lower(): item["score"] for item in output}
            top_label = max(score_map, key=score_map.get)
            results.append({
                "sentence": sent,
                "label": top_label,
                "scores": score_map,
            })

    return results


# ── Hedge Language Ratio ───────────────────────────────────────────────────────

def compute_hedge_ratio(text: str) -> float:
    """
    Fraction of total word tokens that match hedge/qualifier patterns.
    Uses phrase matching so multi-word hedges like 'subject to approval' are caught.
    Returns [0, 1].
    """
    if not text:
        return 0.0
    lower = text.lower()
    words = re.findall(r'\b\w+\b', lower)
    total = len(words)
    if total == 0:
        return 0.0
    # Count phrase matches (each phrase hit counts as one hedge token)
    hedge_count = sum(1 for phrase in _HEDGE_WORDS if phrase in lower)
    return round(min(1.0, hedge_count / max(total, 1)), 4)


# ── Aggregation ────────────────────────────────────────────────────────────────

def _aggregate(sentence_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute aggregate ratios and composite sentiment score from
    per-sentence classification results.

    Composite score = pos_ratio * 1.0  +  neutral_ratio * 0.5  +  neg_ratio * 0.0
                    → [0, 1]  where 1 = all positive, 0 = all negative
    """
    n = len(sentence_results)
    if n == 0:
        return {"pos_ratio": 0.5, "neg_ratio": 0.2, "neu_ratio": 0.3, "sentiment_score": 0.5}

    pos = sum(1 for r in sentence_results if r["label"] == "positive")
    neg = sum(1 for r in sentence_results if r["label"] == "negative")
    neu = n - pos - neg

    pos_ratio = pos / n
    neg_ratio = neg / n
    neu_ratio = neu / n

    composite = pos_ratio * 1.0 + neu_ratio * 0.5 + neg_ratio * 0.0

    return {
        "pos_ratio":       round(pos_ratio, 4),
        "neg_ratio":       round(neg_ratio, 4),
        "neu_ratio":       round(neu_ratio, 4),
        "sentiment_score": round(composite, 4),
        "total_sentences": n,
    }


# ── Trajectory ────────────────────────────────────────────────────────────────

def compute_trajectory(
    score_series: List[float],
    lookback: int = 2,
    threshold: float = 0.05,
) -> str:
    """
    Classify the sentiment trend direction given a chronological list of
    per-period composite scores.

    Parameters
    ----------
    threshold : float
        Minimum delta vs prior average to register as improving/deteriorating.
        Default 0.05 (5pp). Configurable per dataset characteristics.

    Returns: "improving" | "stable" | "deteriorating"
    """
    clean = [s for s in score_series if s is not None]
    if len(clean) < 2:
        return "stable"

    current = clean[-1]
    prior = clean[-(lookback + 1):-1]
    if not prior:
        return "stable"

    prior_avg = statistics.mean(prior)
    delta = current - prior_avg

    if delta > threshold:
        return "improving"
    elif delta < -threshold:
        return "deteriorating"
    return "stable"


# ── Main Analyser Class ───────────────────────────────────────────────────────

class SentimentAnalyser:
    """
    Unified sentiment analyser for EREBUS Module 4.

    Automatically selects FinBERT (if available) or lexicon fallback.
    Always returns the same structured output dictionary regardless of tier.
    """

    def __init__(self, force_lexicon: bool = False):
        """
        Parameters
        ----------
        force_lexicon : bool
            Force the rule-based fallback even if transformers is installed.
            Useful for fast testing without loading the FinBERT model.
        """
        self.use_finbert = _FINBERT_AVAILABLE and not force_lexicon
        tier = "FinBERT (neural)" if self.use_finbert else "Lexicon (rule-based)"
        logger.info(f"SentimentAnalyser initialised — tier: {tier}")

    def analyse_document(
        self,
        text: str,
        historical_scores: Optional[List[float]] = None,
        include_sentences: bool = False,
        trajectory_threshold: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Analyse a financial text document (earnings call, MD&A, etc.).

        Parameters
        ----------
        text : str
            Raw transcript or section text.
        historical_scores : list[float], optional
            Previous period composite scores for trajectory calculation.
        include_sentences : bool
            If True, include per-sentence detail in output.
            Default False — avoids bloating API payload for large transcripts.
        trajectory_threshold : float
            Delta threshold for improving/deteriorating classification (default 0.05).

        Returns
        -------
        dict:
            {
                "sentiment_score": float,     # [0, 1], 1 = fully positive
                "pos_ratio":       float,
                "neg_ratio":       float,
                "neu_ratio":       float,
                "confidence":      float,     # max(pos, neg, neu) — reliability signal
                "total_sentences": int,
                "hedge_ratio":     float,     # [0, 1]
                "trajectory":      str,       # "improving" | "stable" | "deteriorating"
                "tier":            str,       # "finbert" | "lexicon"
                "sentence_results": list | None,
                "data_flags":      list,
            }
        """
        data_flags = []

        if not text or not text.strip():
            data_flags.append("empty_text: no content to analyse")
            return {
                "sentiment_score": 0.5,
                "pos_ratio":       0.33,
                "neg_ratio":       0.33,
                "neu_ratio":       0.34,
                "confidence":      0.34,
                "total_sentences": 0,
                "hedge_ratio":     0.0,
                "trajectory":      "stable",
                "tier":            "none",
                "sentence_results": None,
                "data_flags":      data_flags,
            }

        # Step 1 · Split into sentences
        sentences = split_sentences(text)
        if not sentences:
            data_flags.append("no_sentences_extracted: check input text format")
            sentences = [text]  # treat whole text as one chunk

        # Step 2 · Classify sentences
        if self.use_finbert:
            try:
                sentence_results = _finbert_analyse(sentences)
                tier = "finbert"
            except Exception as e:
                logger.error(f"FinBERT failed, falling back to lexicon: {e}")
                sentence_results = _lexicon_analyse(sentences)
                tier = "lexicon_fallback"
                data_flags.append(f"finbert_fallback: {str(e)[:80]}")
        else:
            sentence_results = _lexicon_analyse(sentences)
            tier = "lexicon"

        # Step 3 · Aggregate
        agg = _aggregate(sentence_results)

        # Step 4 · Hedge ratio
        hedge_ratio = compute_hedge_ratio(text)

        # Step 5 · Trajectory
        hist = list(historical_scores or [])
        hist.append(agg["sentiment_score"])
        trajectory = compute_trajectory(hist, threshold=trajectory_threshold)

        # Step 6 · Confidence = dominant class fraction
        confidence = round(max(agg["pos_ratio"], agg["neg_ratio"], agg["neu_ratio"]), 4)

        return {
            "sentiment_score":  agg["sentiment_score"],
            "pos_ratio":        agg["pos_ratio"],
            "neg_ratio":        agg["neg_ratio"],
            "neu_ratio":        agg["neu_ratio"],
            "confidence":       confidence,
            "total_sentences":  agg["total_sentences"],
            "hedge_ratio":      hedge_ratio,
            "trajectory":       trajectory,
            "tier":             tier,
            "sentence_results": sentence_results if include_sentences else None,
            "data_flags":       data_flags,
        }

    def analyse_series(
        self,
        texts: List[str],
    ) -> Dict[str, Any]:
        """
        Analyse multiple periods of text chronologically and compute
        the full trajectory across them.

        Parameters
        ----------
        texts : list[str]
            Ordered list of transcript/MDA texts (oldest first).

        Returns
        -------
        dict:
            {
                "period_results": list[dict],   # per-period analyse_document() output
                "score_series":   list[float],  # composite scores per period
                "trajectory":     str,          # overall trend direction
                "avg_score":      float,
                "avg_hedge_ratio": float,
            }
        """
        period_results = []
        score_series = []

        for i, text in enumerate(texts):
            result = self.analyse_document(text, historical_scores=score_series.copy())
            period_results.append(result)
            score_series.append(result["sentiment_score"])

        overall_trajectory = compute_trajectory(score_series)
        avg_score = round(statistics.mean(score_series), 4) if score_series else 0.5
        avg_hedge = round(
            statistics.mean(r["hedge_ratio"] for r in period_results), 4
        ) if period_results else 0.0

        return {
            "period_results":  period_results,
            "score_series":    score_series,
            "trajectory":      overall_trajectory,
            "avg_score":       avg_score,
            "avg_hedge_ratio": avg_hedge,
        }
