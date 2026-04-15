"""
EREBUS — Comparison LLM Explainer (Groq)
==========================================
Uses Groq's OpenAI-compatible API to generate a concise, structured
comparison narrative. Falls back gracefully if GROQ_API_KEY is absent.

Required env var: GROQ_API_KEY
Optional:         GROQ_MODEL   (default: llama3-8b-8192)
"""

from __future__ import annotations
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_GROQ_BASE_URL  = "https://api.groq.com/openai/v1"
_DEFAULT_MODEL  = "llama3-8b-8192"


def _build_prompt(
    id_a: str,
    id_b: str,
    summary: dict,
    metrics: dict,
    key_diffs: list[str],
) -> str:
    winner      = summary.get("winner", "unclear")
    confidence  = summary.get("confidence", 0.0)
    cat_winners = summary.get("category_winners", {})

    def _fmt(v, unit="", default="N/A"):
        if v is None:
            return default
        try:
            return f"{float(v):.1f}{unit}"
        except (TypeError, ValueError):
            return str(v)

    def _both(key, unit=""):
        row = metrics.get(key, {})
        va  = _fmt(row.get(id_a), unit)
        vb  = _fmt(row.get(id_b), unit)
        return f"{id_a}: {va}  |  {id_b}: {vb}"

    lines = [
        f"You are EREBUS, an elite Indian equity research analyst.",
        f"Write a concise, professional comparison of {id_a} vs {id_b} (5–8 sentences).",
        f"",
        f"## Key Metrics",
        f"Revenue:        {_both('revenue', ' Cr')}",
        f"Net Income:     {_both('net_income', ' Cr')}",
        f"Rev Growth:     {_both('revenue_growth', '%')}",
        f"Profit Margin:  {_both('profit_margin', '%')}",
        f"ROE:            {_both('roe', '%')}",
        f"Risk Score:     {_both('risk_score')}",
        f"CAS (Alpha):    {_both('cas')}",
        f"Momentum:       {_both('momentum')}",
        f"RSI:            {_both('rsi')}",
        f"",
        f"## Category Winners",
        f"Performance:  {cat_winners.get('performance', 'tie')}",
        f"Risk:         {cat_winners.get('risk', 'tie')}",
        f"Alpha:        {cat_winners.get('alpha', 'tie')}",
        f"Technical:    {cat_winners.get('technical', 'tie')}",
        f"",
        f"## Key Differences",
    ] + [f"- {d}" for d in key_diffs] + [
        f"",
        f"## Your Task",
        f"Write a 5-8 sentence analysis that:",
        f"1. Highlights each company's strengths and weaknesses",
        f"2. Explains why the category winners lead in their dimension",
        f"3. States a clear final verdict: '{winner}' wins with {confidence*100:.0f}% confidence",
        f"",
        f"Tone: precise, data-driven, professional. NO generic filler. NO bullet points in output.",
        f"Start directly with the analysis.",
    ]
    return "\n".join(lines)


def generate_explanation(
    id_a:      str,
    id_b:      str,
    summary:   dict,
    metrics:   dict,
    key_diffs: list[str],
) -> Optional[str]:
    """
    Generate LLM comparison narrative via Groq.
    Returns None (not raises) if Groq is unavailable or fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.info("[compare/llm] GROQ_API_KEY not set — skipping LLM explanation")
        return _fallback_explanation(id_a, id_b, summary, key_diffs)

    model  = os.getenv("GROQ_MODEL", _DEFAULT_MODEL)
    prompt = _build_prompt(id_a, id_b, summary, metrics, key_diffs)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are EREBUS, a world-class Indian equity research analyst. "
                        "Provide precise, data-driven analysis. Never speculate without data."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        text = resp.choices[0].message.content.strip()
        logger.info("[compare/llm] Groq explanation generated (%d chars)", len(text))
        return text

    except Exception as e:
        logger.warning("[compare/llm] Groq call failed: %s", e)
        return _fallback_explanation(id_a, id_b, summary, key_diffs)


def _fallback_explanation(
    id_a: str,
    id_b: str,
    summary: dict,
    key_diffs: list[str],
) -> str:
    """Rule-based explanation when Groq is unavailable."""
    winner     = summary.get("winner", "unclear")
    confidence = summary.get("confidence", 0.0)
    cat_w      = summary.get("category_winners", {})

    lines = [
        f"EREBUS Comparison: {id_a} vs {id_b}",
        "",
        f"Category leaders — "
        f"Performance: {cat_w.get('performance', 'tie')}, "
        f"Risk: {cat_w.get('risk', 'tie')}, "
        f"Alpha: {cat_w.get('alpha', 'tie')}, "
        f"Technical: {cat_w.get('technical', 'tie')}.",
        "",
    ] + key_diffs + [
        "",
        f"Verdict: {winner} leads overall with {confidence*100:.0f}% confidence based on "
        "EREBUS's weighted scoring across performance, alpha, risk, and technicals."
        " (Enable GROQ_API_KEY for a full LLM narrative.)",
    ]
    return "\n".join(lines)
