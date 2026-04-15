# ranking/router.py - REAL S3 DATA ONLY

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from modules.ranking.ranker import get_ranker

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/")
async def get_rankings(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    min_cas: Optional[float] = Query(None, ge=-100, le=100, description="Minimum CAS score"),
    max_risk: Optional[float] = Query(None, ge=0, le=100, description="Maximum risk score"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    refresh: bool = Query(False, description="Force refresh from S3"),
) -> List[dict]:
    """
    Get ranked list of companies from S3 data.
    """
    ranker = get_ranker()
    ranked = ranker.get_ranked_companies(
        force_refresh=refresh,
        sector=sector,
        min_cas=min_cas,
        max_risk=max_risk,
    )
    return ranked[:limit]


@router.get("/leaderboard")
async def get_leaderboard(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top companies"),
) -> dict:
    """
    Get leaderboard summary from real S3 data.
    """
    ranker = get_ranker()
    return ranker.get_leaderboard(top_n=top_n, sector=sector)


@router.get("/company/{company_id}")
async def get_company_card(company_id: str) -> dict:
    """
    Get detailed signal card for a specific company from S3.
    """
    ranker = get_ranker()
    card = ranker.get_company_signal_card(company_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return card


@router.get("/sectors")
async def get_sectors() -> List[str]:
    """
    Get list of all available sectors from S3 data.
    """
    ranker = get_ranker()
    universe = ranker.get_universe()
    sectors = set(c.get("sector", "Unknown") for c in universe)
    return sorted(list(sectors))


@router.post("/refresh")
async def refresh_universe() -> dict:
    """
    Force refresh company universe from S3.
    """
    ranker = get_ranker()
    universe = ranker.refresh_universe()
    return {
        "status": "refreshed",
        "total_companies": len(universe),
    }


@router.get("/health")
async def health_check() -> dict:
    """
    Health check with S3 connection status.
    """
    try:
        ranker = get_ranker()
        universe = ranker.get_universe()
        return {
            "status": "healthy",
            "total_companies": len(universe),
            "data_source": "S3",
            "module": "ranking",
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "data_source": "S3",
            "module": "ranking",
        }