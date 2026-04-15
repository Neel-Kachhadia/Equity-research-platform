"""
Module 7: Ranking & Filtering Engine

Pure functional ranking and filtering logic for company alpha scores.
No database dependencies in core logic - completely testable.
"""

from .ranking import (
    # Core functions
    compute_ranking,
    filter_companies,
    build_signal_card,
    build_leaderboard_summary,
    compare_companies,
    
    # Helpers
    get_risk_level,
    get_key_signals,
    get_top_bottom_signals,
    normalize_alpha_scores,
    validate_company_data,
    
    # Constants
    SIGNAL_THRESHOLD,
    CAS_RANGE,
    RISK_RANGE,
    RISK_BANDS,
)

# No mock data imports — all ranking data comes from live S3 pipeline

# Import router for FastAPI endpoints
from .router import router

# Import ranker service (optional, for future DB integration)
from .ranker import Ranker, get_ranker

__all__ = [
    # Core API
    "compute_ranking",
    "filter_companies",
    "build_signal_card",
    "build_leaderboard_summary",
    "compare_companies",
    
    # Helpers
    "get_risk_level",
    "get_key_signals",
    "get_top_bottom_signals",
    "normalize_alpha_scores",
    "validate_company_data",
    
    # Constants
    "SIGNAL_THRESHOLD",
    "CAS_RANGE",
    "RISK_RANGE",
    "RISK_BANDS",

    # Router
    "router",

    # Ranker service
    "Ranker",
    "get_ranker",
]


__version__ = "0.1.0"