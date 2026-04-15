# ranker.py - REAL S3 DATA ONLY

"""
Ranker service - Uses real company data from S3.
No mock data dependencies.
"""

from typing import List, Dict, Any, Optional
import logging

from .ranking import (
    compute_ranking,
    filter_companies,
    build_signal_card,
    build_leaderboard_summary,
)

logger = logging.getLogger(__name__)


class Ranker:
    """
    Service class for ranking operations.
    Uses real company data from S3/PostgreSQL.
    """
    
    _instance = None
    _universe: Optional[List[Dict[str, Any]]] = None
    _ranked_universe: Optional[List[Dict[str, Any]]] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, use_cache: bool = True):
        if hasattr(self, '_initialized'):
            return
        
        self.use_cache = use_cache
        self._initialized = True
        logger.info("[Ranker] Initialized - using real S3 data")
    
    @classmethod
    def load_universe_from_s3(cls, company_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Load company universe from S3.
        Fetches financial data and computes CAS for all companies.
        """
        from modules.ingestion.company_loader import load_company
        from modules.quant import compute_quant_profile
        from modules.alpha import AlphaInput, run_all_alphas
        
        universe = []
        
        # If no company_ids provided, list from S3
        if company_ids is None:
            company_ids = cls._list_companies_in_s3()
        
        logger.info("[Ranker] Loading %d companies from S3", len(company_ids))
        
        for company_id in company_ids:
            try:
                # Load from S3
                ctx = load_company(company_id)
                
                # Compute quant profile
                quant = compute_quant_profile(
                    prices=ctx["prices"],
                    financials=ctx["financials"],
                )
                
                # Compute alpha
                alpha_input = AlphaInput(**ctx["alpha_fields"])
                alpha = run_all_alphas(alpha_input)
                
                # Build company entry
                company_entry = {
                    "company_id": company_id,
                    "sector": ctx["alpha_fields"].get("sector", "Unknown"),
                    "cas": alpha.get("composite", {}).get("cas", 0.0),
                    "risk_score": quant.get("risk", {}).get("overall_risk_score", 50.0) if quant else 50.0,
                    "alpha_scores": alpha.get("signals", {}),
                    "quant_profile": quant,
                    "alpha_profile": alpha,
                }
                
                universe.append(company_entry)
                logger.debug("[Ranker] Loaded %s - CAS: %.2f", company_id, company_entry["cas"])
                
            except Exception as e:
                logger.warning("[Ranker] Failed to load %s: %s", company_id, e)
                continue
        
        return universe
    
    @classmethod
    def _list_companies_in_s3(cls) -> List[str]:
        """List all company folders in S3 bucket."""
        import boto3
        import os
        
        bucket = os.getenv("S3_BUCKET_NAME", "erebus-data-prod")
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
        )
        
        companies = set()
        paginator = s3.get_paginator("list_objects_v2")

        # Folders that are NOT company tickers
        _SYSTEM_PREFIXES = {
            "uploads", "ocr-uploads", "ocr_uploads",
            "tmp", "temp", "backup", "backups", "archive",
            "logs", "cache", "system", "config",
        }

        for page in paginator.paginate(Bucket=bucket, Delimiter="/"):
            for prefix in page.get("CommonPrefixes", []):
                folder = prefix["Prefix"].rstrip("/")
                if folder and not folder.startswith(".") and folder.lower() not in _SYSTEM_PREFIXES:
                    companies.add(folder)

        return sorted(list(companies))
    
    @classmethod
    def get_universe(cls, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get the company universe from S3 with caching."""
        if cls._universe is None or force_refresh:
            logger.info("[Ranker] Loading universe from S3...")
            cls._universe = cls.load_universe_from_s3()
            cls._ranked_universe = None  # Invalidate ranked cache
            logger.info("[Ranker] Loaded %d companies", len(cls._universe))
        
        return cls._universe
    
    def get_ranked_companies(
        self,
        force_refresh: bool = False,
        sector: Optional[str] = None,
        min_cas: Optional[float] = None,
        max_risk: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Get ranked companies with optional filtering."""
        # Get universe
        universe = self.get_universe(force_refresh)
        
        # Compute ranking if needed
        if self._ranked_universe is None or force_refresh:
            self._ranked_universe = compute_ranking(universe)
        
        # Apply filters
        return filter_companies(self._ranked_universe, sector, min_cas, max_risk)
    
    def get_company_signal_card(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed signal card for a single company."""
        ranked = self.get_ranked_companies()
        return build_signal_card(company_id, ranked)
    
    def get_leaderboard(self, top_n: int = 10, sector: Optional[str] = None) -> Dict[str, Any]:
        """Get leaderboard summary."""
        ranked = self.get_ranked_companies(sector=sector)
        return build_leaderboard_summary(ranked, top_n)
    
    def refresh_universe(self) -> None:
        """Force refresh from S3."""
        self.__class__._universe = None
        self.__class__._ranked_universe = None
        return self.get_universe(force_refresh=True)


# Singleton accessor
_ranker_instance = None


def get_ranker(use_cache: bool = True) -> Ranker:
    """Get or create singleton Ranker instance."""
    global _ranker_instance
    if _ranker_instance is None:
        _ranker_instance = Ranker(use_cache=use_cache)
    return _ranker_instance