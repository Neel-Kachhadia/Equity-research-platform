"""
Module: Analysis Orchestration
================================
Integration layer connecting all EREBUS modules.

Usage:
    from modules.analysis import analyze_company

    # Normal mode: quant + alpha + ranking
    result = analyze_company("RELIANCE", mode="normal")

    # Deep mode: + RAG retrieval + LLM narrative
    result = analyze_company("RELIANCE", mode="deep")
"""

from .orchestrator import analyze_company, AnalysisMode

__all__ = ["analyze_company", "AnalysisMode"]
__version__ = "0.1.0"
