"""
Core ranking and filtering logic for Module 7.
No database, no side-effects, pure functions only.
"""

from typing import List, Dict, Any, Optional, Tuple


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

SIGNAL_THRESHOLD = 10.0  # abs(score) must exceed this to be a "key signal"
CAS_RANGE = (-100.0, 100.0)  # Valid range for CAS scores
RISK_RANGE = (0.0, 100.0)   # Valid range for risk scores

RISK_BANDS = [
    (0, 30, "low"),
    (30, 70, "medium"),
    (70, 100, "high"),
]


# ── VALIDATION HELPERS ───────────────────────────────────────────────────────

def validate_company_data(company: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate required fields in company data.
    Returns (is_valid, error_message).
    """
    required_fields = ["company_id", "sector", "cas", "risk_score", "alpha_scores"]
    
    for field in required_fields:
        if field not in company:
            return False, f"Missing required field: {field}"
    
    # Validate CAS range
    cas = company["cas"]
    if not (CAS_RANGE[0] <= cas <= CAS_RANGE[1]):
        return False, f"CAS score {cas} out of valid range {CAS_RANGE}"
    
    # Validate risk range
    risk = company["risk_score"]
    if not (RISK_RANGE[0] <= risk <= RISK_RANGE[1]):
        return False, f"Risk score {risk} out of valid range {RISK_RANGE}"
    
    # Validate alpha_scores is a dict
    if not isinstance(company["alpha_scores"], dict):
        return False, "alpha_scores must be a dictionary"
    
    return True, None


# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_risk_level(risk_score: float) -> str:
    """
    Map risk_score (0–100) to a human-readable level.

    Thresholds:
        0  – 30  → low
        30 – 70  → medium
        70 – 100 → high
    """
    for low, high, label in RISK_BANDS:
        if low <= risk_score < high:
            return label
    return "high"  # Anything >= 100 treated as high


def get_key_signals(alpha_scores: Dict[str, float], top_n: int = 2) -> List[str]:
    """
    Return the top_n alpha drivers with abs(score) > SIGNAL_THRESHOLD.
    Sorted by absolute value descending so the strongest driver comes first.

    If no signals exceed the threshold, returns an empty list.
    This avoids misleading "top signals" when all scores are near zero or negative.
    """
    if not alpha_scores:
        return []
    
    meaningful = {
        k: v for k, v in alpha_scores.items()
        if abs(v) > SIGNAL_THRESHOLD
    }

    sorted_signals = sorted(meaningful, key=lambda k: abs(meaningful[k]), reverse=True)
    return sorted_signals[:top_n]


def get_top_bottom_signals(alpha_scores: Dict[str, float]) -> Tuple[Optional[str], Optional[str]]:
    """
    Get the strongest (highest) and weakest (lowest) signals.
    Returns (strongest, weakest) tuple.
    """
    if not alpha_scores:
        return None, None
    
    strongest = max(alpha_scores, key=lambda k: alpha_scores[k])
    weakest = min(alpha_scores, key=lambda k: alpha_scores[k])
    return strongest, weakest


def normalize_alpha_scores(alpha_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize alpha scores to [-100, 100] range.
    Useful if scores come from different models with different scales.
    """
    if not alpha_scores:
        return {}
    
    values = list(alpha_scores.values())
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return {k: 0.0 for k in alpha_scores}
    
    normalized = {}
    for k, v in alpha_scores.items():
        # Scale to [-100, 100]
        normalized[k] = 200 * (v - min_val) / (max_val - min_val) - 100
    
    return normalized


# ── CORE LOGIC ────────────────────────────────────────────────────────────────

def compute_ranking(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort companies by CAS descending.
    Tiebreaker order:
        1. CAS          (descending)
        2. risk_score   (ascending  — lower risk preferred)
        3. company_id   (ascending  — stable alphabetical fallback)

    Returns a NEW list with a "rank" field added.
    Original input is never mutated.
    """
    if not companies:
        return []
    
    # Filter out invalid companies
    valid_companies = []
    for company in companies:
        is_valid, error = validate_company_data(company)
        if is_valid:
            valid_companies.append(company)
    
    sorted_companies = sorted(
        valid_companies,
        key=lambda c: (-c["cas"], c["risk_score"], c["company_id"])
    )

    ranked = []
    for rank, company in enumerate(sorted_companies, start=1):
        ranked.append({**company, "rank": rank})

    return ranked


def filter_companies(
    companies: List[Dict[str, Any]],
    sector: Optional[str] = None,
    min_cas: Optional[float] = None,
    max_risk: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Filter a list of companies. All parameters are optional.
    Missing / None parameters are ignored (no filter applied for that dimension).

    Args:
        companies:  List of company dicts (may already be ranked)
        sector:     Exact sector match (case-insensitive)
        min_cas:    Minimum CAS score (inclusive), range [-100, 100]
        max_risk:   Maximum risk score (inclusive), range [0, 100]

    Returns:
        Filtered list. May be empty — never raises.
    """
    result = companies

    if sector is not None:
        result = [c for c in result if c.get("sector", "").lower() == sector.lower()]

    if min_cas is not None:
        result = [c for c in result if c.get("cas", -101) >= min_cas]

    if max_risk is not None:
        result = [c for c in result if c.get("risk_score", 101) <= max_risk]

    return result


def build_signal_card(
    company_id: str,
    ranked_list: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Build a detailed signal card for a single company using the ranked list.
    Rank is derived from the ranked list — no mismatch possible.

    Returns None if company_id is not found.
    """
    company = next((c for c in ranked_list if c["company_id"] == company_id), None)
    if not company:
        return None

    alpha = company.get("alpha_scores", {})
    key_signals = get_key_signals(alpha)
    strongest, weakest = get_top_bottom_signals(alpha)

    return {
        "rank": company["rank"],
        "company_id": company["company_id"],
        "sector": company.get("sector", "unknown"),
        "cas": company["cas"],
        "alpha_breakdown": alpha,
        "risk_score": company["risk_score"],
        "key_signals": key_signals,
        "summary": {
            "strongest_signal": strongest,
            "weakest_signal": weakest,
            "risk_level": get_risk_level(company["risk_score"]),
            "has_meaningful_signals": len(key_signals) > 0,
            "total_signals": len(alpha),
        },
    }


def build_leaderboard_summary(
    ranked_companies: List[Dict[str, Any]],
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Build a summary view of the leaderboard.
    
    Returns:
        Dictionary with top performers, sector breakdown, and statistics.
    """
    if not ranked_companies:
        return {
            "total_companies": 0,
            "top_performers": [],
            "sector_breakdown": {},
            "avg_cas": 0.0,
            "avg_risk": 0.0,
        }
    
    top_performers = [
        {
            "rank": c["rank"],
            "company_id": c["company_id"],
            "sector": c.get("sector", "unknown"),
            "cas": c["cas"],
            "risk_score": c["risk_score"],
            "risk_level": get_risk_level(c["risk_score"]),
            "key_signals": get_key_signals(c.get("alpha_scores", {}), top_n=1),
        }
        for c in ranked_companies[:top_n]
    ]
    
    # Sector breakdown
    sectors = {}
    for company in ranked_companies:
        sector = company.get("sector", "unknown")
        if sector not in sectors:
            sectors[sector] = {"count": 0, "total_cas": 0, "avg_cas": 0}
        sectors[sector]["count"] += 1
        sectors[sector]["total_cas"] += company["cas"]
    
    for sector_data in sectors.values():
        if sector_data["count"] > 0:
            sector_data["avg_cas"] = sector_data["total_cas"] / sector_data["count"]
    
    # Overall statistics
    total_cas = sum(c["cas"] for c in ranked_companies)
    total_risk = sum(c["risk_score"] for c in ranked_companies)
    n = len(ranked_companies)
    
    # Find best performing sector
    best_sector = None
    best_avg_cas = -101
    for sector, data in sectors.items():
        if data["avg_cas"] > best_avg_cas:
            best_avg_cas = data["avg_cas"]
            best_sector = sector
    
    return {
        "total_companies": n,
        "top_performers": top_performers,
        "sector_breakdown": sectors,
        "avg_cas": total_cas / n if n > 0 else 0.0,
        "avg_risk": total_risk / n if n > 0 else 0.0,
        "best_sector": best_sector,
    }


def compare_companies(
    company_ids: List[str],
    ranked_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare multiple companies side-by-side.
    
    Args:
        company_ids: List of company IDs to compare
        ranked_list: Ranked list of companies
        
    Returns:
        Comparison dictionary with company details and relative metrics
    """
    companies = []
    for cid in company_ids:
        company = next((c for c in ranked_list if c["company_id"] == cid), None)
        if company:
            companies.append(company)
    
    if not companies:
        return {"companies": [], "comparison": {}}
    
    # Calculate comparison metrics
    avg_cas = sum(c["cas"] for c in companies) / len(companies)
    avg_risk = sum(c["risk_score"] for c in companies) / len(companies)
    
    # Find common key signals
    all_signals = {}
    for company in companies:
        signals = get_key_signals(company.get("alpha_scores", {}), top_n=3)
        for signal in signals:
            all_signals[signal] = all_signals.get(signal, 0) + 1
    
    common_signals = [
        signal for signal, count in all_signals.items()
        if count >= len(companies) * 0.5  # Present in at least 50% of companies
    ]
    
    return {
        "companies": [
            {
                "company_id": c["company_id"],
                "rank": c["rank"],
                "sector": c.get("sector", "unknown"),
                "cas": c["cas"],
                "risk_score": c["risk_score"],
                "risk_level": get_risk_level(c["risk_score"]),
                "key_signals": get_key_signals(c.get("alpha_scores", {})),
            }
            for c in companies
        ],
        "comparison": {
            "avg_cas": avg_cas,
            "avg_risk": avg_risk,
            "cas_spread": max(c["cas"] for c in companies) - min(c["cas"] for c in companies),
            "risk_spread": max(c["risk_score"] for c in companies) - min(c["risk_score"] for c in companies),
            "common_signals": common_signals,
        },
    }