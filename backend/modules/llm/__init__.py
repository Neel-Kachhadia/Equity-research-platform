"""
Module: LLM Integration
=======================
Entry point for all LLM-powered financial analysis.

Usage:
    from modules.llm import generate_financial_analysis, LLMProvider

    analysis = generate_financial_analysis(
        provider=LLMProvider.OPENAI,
        analysis_type="company_summary",
        context={"company": "RELIANCE", "sector": "Energy"}
    )

Provider Support:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Ollama (Local models)
"""

import dataclasses
from typing import Dict, Any, Optional, List
from enum import Enum

from .generator import (
    LLMProvider,
    LLMGenerator,
    get_generator,
    generate_text,
    generate_structured,
)
from .prompt_builder import (
    PromptTemplate,
    build_prompt,
    build_system_prompt,
    build_financial_prompt,
)
from .financial_prompts import (
    COMPANY_SUMMARY_TEMPLATE,
    EARNINGS_ANALYSIS_TEMPLATE,
    RISK_ASSESSMENT_TEMPLATE,
    SENTIMENT_ANALYSIS_TEMPLATE,
    QUANT_INTERPRETATION_TEMPLATE,
)

__version__ = "0.1.0"

__all__ = [
    "LLMProvider",
    "LLMGenerator",
    "get_generator",
    "generate_text",
    "generate_structured",
    "PromptTemplate",
    "build_prompt",
    "build_system_prompt",
    "build_financial_prompt",
    "generate_financial_analysis",
    "analyze_company",
    "interpret_quant_profile",
]


def generate_financial_analysis(
    provider: LLMProvider,
    analysis_type: str,
    context: Dict[str, Any],
    model: Optional[str] = None,
    temperature: float = 0.3,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    Generate financial analysis using specified provider.
    
    Returns:
        Dict with text and metadata (serializable for FastAPI)
    """
    template_map = {
        "company_summary": COMPANY_SUMMARY_TEMPLATE,
        "earnings_analysis": EARNINGS_ANALYSIS_TEMPLATE,
        "risk_assessment": RISK_ASSESSMENT_TEMPLATE,
        "sentiment_analysis": SENTIMENT_ANALYSIS_TEMPLATE,
        "quant_interpretation": QUANT_INTERPRETATION_TEMPLATE,
    }
    
    template = template_map.get(analysis_type)
    if not template:
        raise ValueError(f"Unknown analysis_type: {analysis_type}")
    
    system_prompt = build_system_prompt("financial_analyst")
    user_prompt = build_financial_prompt(template, context)
    
    generator = get_generator(provider)
    result = generator.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        stream=stream,
    )
    
    # Convert dataclass to dict for FastAPI serialization
    return dataclasses.asdict(result)


def analyze_company(
    company_id: str,
    quant_profile: Optional[Dict[str, Any]] = None,
    document_context: Optional[List[str]] = None,
    provider: LLMProvider = LLMProvider.OPENAI,
) -> Dict[str, Any]:
    """
    High-level orchestrator for comprehensive company analysis.
    """
    context = {
        "company_id": company_id,
        "quant_profile": quant_profile or {},
        "document_context": document_context or [],
    }
    
    results = {}
    
    results["summary"] = generate_financial_analysis(
        provider=provider,
        analysis_type="company_summary",
        context=context,
    )
    
    if quant_profile:
        results["quant_interpretation"] = interpret_quant_profile(
            provider=provider,
            quant_profile=quant_profile,
            company_id=company_id,
        )
    
    if quant_profile and quant_profile.get("risk"):
        context["risk_profile"] = quant_profile["risk"]
        results["risk_assessment"] = generate_financial_analysis(
            provider=provider,
            analysis_type="risk_assessment",
            context=context,
        )
    
    from datetime import datetime
    return {
        "company_id": company_id,
        "analyses": results,
        "provider": provider.value,
        "generated_at": datetime.utcnow().isoformat(),
    }


def interpret_quant_profile(
    provider: LLMProvider,
    quant_profile: Dict[str, Any],
    company_id: str,
) -> Dict[str, Any]:
    """
    Generate natural language interpretation of quantitative metrics.
    """
    context = {
        "company_id": company_id,
        "ratios": quant_profile.get("ratios", {}),
        "trends": quant_profile.get("trends", {}),
        "volatility": quant_profile.get("volatility", {}),
        "risk": quant_profile.get("risk", {}),
    }
    
    return generate_financial_analysis(
        provider=provider,
        analysis_type="quant_interpretation",
        context=context,
        temperature=0.2,
    )