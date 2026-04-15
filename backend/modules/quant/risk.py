"""
Risk scoring and assessment.
Combines outputs from ratios, trends, and volatility modules.
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


# ── RISK SCORE CALCULATION ───────────────────────────────────────────────────

def compute_all_risk(
    ratios: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    volatility: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive risk assessment from module outputs.
    
    This function takes the OUTPUTS of ratios, trends, and volatility -
    NOT raw inputs. It enforces the dependency order.
    
    Args:
        ratios: Output from compute_all_ratios()
        trends: Output from compute_all_trends()
        volatility: Output from compute_all_volatility()
        
    Returns:
        {
            "overall_risk_score": 0-100,
            "risk_category": "low"|"medium"|"high",
            "financial_risk": {...},
            "market_risk": {...},
            "volatility_risk": {...},
            "risk_factors": [...],
            "warnings": [...]
        }
    """
    risk_assessment = {
        "overall_risk_score": 50.0,  # Default neutral
        "risk_category": "medium",
        "financial_risk": _assess_financial_risk(ratios),
        "market_risk": _assess_market_risk(trends),
        "volatility_risk": _assess_volatility_risk(volatility),
        "risk_factors": [],
        "warnings": [],
    }
    
    # Calculate weighted overall risk score
    weights = {
        "financial": 0.35,
        "market": 0.30,
        "volatility": 0.35,
    }
    
    overall = 0
    total_weight = 0
    
    if risk_assessment["financial_risk"]["score"] is not None:
        overall += risk_assessment["financial_risk"]["score"] * weights["financial"]
        total_weight += weights["financial"]
    
    if risk_assessment["market_risk"]["score"] is not None:
        overall += risk_assessment["market_risk"]["score"] * weights["market"]
        total_weight += weights["market"]
    
    if risk_assessment["volatility_risk"]["score"] is not None:
        overall += risk_assessment["volatility_risk"]["score"] * weights["volatility"]
        total_weight += weights["volatility"]
    
    if total_weight > 0:
        risk_assessment["overall_risk_score"] = overall / total_weight
    
    # Determine risk category
    score = risk_assessment["overall_risk_score"]
    if score < 30:
        risk_assessment["risk_category"] = "low"
    elif score < 70:
        risk_assessment["risk_category"] = "medium"
    else:
        risk_assessment["risk_category"] = "high"
    
    # Collect risk factors
    risk_assessment["risk_factors"] = _collect_risk_factors(risk_assessment)
    risk_assessment["warnings"] = _collect_warnings(risk_assessment)
    
    return risk_assessment


def _assess_financial_risk(ratios: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess financial risk from ratios."""
    if not ratios:
        return {"score": None, "factors": [], "assessment": "insufficient_data"}
    
    score = 50
    factors = []
    
    # Leverage risk (higher debt = higher risk)
    debt_to_equity = ratios.get('debt_to_equity')
    if debt_to_equity is not None:
        if debt_to_equity > 2.0:
            score += 20
            factors.append(f"High leverage (D/E: {debt_to_equity:.2f})")
        elif debt_to_equity > 1.0:
            score += 10
            factors.append(f"Moderate leverage (D/E: {debt_to_equity:.2f})")
        elif debt_to_equity < 0.3:
            score -= 10
            factors.append(f"Low leverage (D/E: {debt_to_equity:.2f})")
    
    # Interest coverage (lower coverage = higher risk)
    interest_coverage = ratios.get('interest_coverage')
    if interest_coverage is not None:
        if interest_coverage < 1.5:
            score += 25
            factors.append(f"Poor interest coverage: {interest_coverage:.2f}x")
        elif interest_coverage < 3.0:
            score += 10
            factors.append(f"Low interest coverage: {interest_coverage:.2f}x")
        elif interest_coverage > 10:
            score -= 10
            factors.append(f"Strong interest coverage: {interest_coverage:.2f}x")
    
    # Profitability (lower margins = higher risk)
    net_margin = ratios.get('net_margin')
    if net_margin is not None:
        if net_margin < 0:
            score += 30
            factors.append("Negative net margin")
        elif net_margin < 0.05:
            score += 15
            factors.append(f"Low profitability: {net_margin:.1%}")
        elif net_margin > 0.20:
            score -= 10
            factors.append(f"Excellent profitability: {net_margin:.1%}")
        elif net_margin > 0.15:
            score -= 7
            factors.append(f"Strong profitability: {net_margin:.1%}")
        elif net_margin > 0.10:
            score -= 3
            factors.append(f"Solid profitability: {net_margin:.1%}")

    # ROE quality — high ROE signals capital efficiency (lower risk)
    roe = ratios.get('return_on_equity')
    if roe is not None and 0 < roe < 5:   # cap at 5x to ignore proxy inflation
        if roe > 0.40:
            score -= 8
            factors.append(f"High capital efficiency (ROE: {roe:.1%})")
        elif roe > 0.20:
            score -= 4
            factors.append(f"Good capital efficiency (ROE: {roe:.1%})")
        elif roe < 0.05:
            score += 10
            factors.append(f"Low ROE: {roe:.1%}")

    # Liquidity (lower liquidity = higher risk)
    current_ratio = ratios.get('current_ratio')
    if current_ratio is not None:
        if current_ratio < 1.0:
            score += 20
            factors.append(f"Liquidity concern (Current ratio: {current_ratio:.2f})")
        elif current_ratio < 1.5:
            score += 10
            factors.append(f"Tight liquidity (Current ratio: {current_ratio:.2f})")
        elif current_ratio > 3.0:
            score -= 5
            factors.append(f"Strong liquidity (Current ratio: {current_ratio:.2f})")

    # Clamp score
    score = max(0, min(100, score))

    
    return {
        "score": score,
        "factors": factors,
        "assessment": "high" if score > 70 else "medium" if score > 30 else "low",
    }


def _assess_market_risk(trends: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess market/trend risk."""
    if not trends:
        return {"score": None, "factors": [], "assessment": "insufficient_data"}
    
    score = 50
    factors = []
    
    # Trend direction
    current_trend = trends.get('current_trend')
    if current_trend == "bearish":
        score += 20
        factors.append("Bearish trend")
    elif current_trend == "bullish":
        score -= 15
        factors.append("Bullish trend")
    
    # RSI (overbought/oversold)
    rsi = trends.get('current_rsi')
    if rsi is not None:
        if rsi > 70:
            score += 10
            factors.append(f"Overbought (RSI: {rsi:.1f})")
        elif rsi < 30:
            score -= 5
            factors.append(f"Oversold (RSI: {rsi:.1f})")
    
    # Price vs moving averages
    price_vs_sma50 = trends.get('price_vs_sma50')
    if price_vs_sma50 is not None:
        if price_vs_sma50 < -10:
            score += 15
            factors.append(f"Trading below 50-day MA ({price_vs_sma50:.1f}%)")
        elif price_vs_sma50 > 10:
            score -= 10
            factors.append(f"Trading above 50-day MA ({price_vs_sma50:.1f}%)")
    
    price_vs_sma200 = trends.get('price_vs_sma200')
    if price_vs_sma200 is not None:
        if price_vs_sma200 < -15:
            score += 20
            factors.append(f"Below 200-day MA ({price_vs_sma200:.1f}%) - Bear market territory")
        elif price_vs_sma200 < 0:
            score += 10
            factors.append(f"Below 200-day MA ({price_vs_sma200:.1f}%)")
    
    # MACD
    macd = trends.get('macd', {})
    histogram = macd.get('histogram')
    if histogram is not None:
        if histogram < 0:
            score += 5
        else:
            score -= 5
    
    # Clamp score
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "factors": factors,
        "assessment": "high" if score > 70 else "medium" if score > 30 else "low",
    }


def _assess_volatility_risk(volatility: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess volatility risk."""
    if not volatility:
        return {"score": None, "factors": [], "assessment": "insufficient_data"}
    
    score = 50
    factors = []
    
    # Volatility regime
    regime = volatility.get('regime', {})
    current_regime = regime.get('current_regime')
    if current_regime == "high":
        score += 25
        factors.append("High volatility regime")
    elif current_regime == "low":
        score -= 10
        factors.append("Low volatility regime")
    
    # Current volatility level
    current_vol = volatility.get('current_volatility_20d')
    if current_vol is not None:
        if current_vol > 0.40:  # 40% annualized
            score += 20
            factors.append(f"Extreme volatility: {current_vol:.1%}")
        elif current_vol > 0.25:
            score += 10
            factors.append(f"High volatility: {current_vol:.1%}")
        elif current_vol < 0.15:
            score -= 10
            factors.append(f"Low volatility: {current_vol:.1%}")
    
    # Max drawdown
    max_dd = volatility.get('max_drawdown')
    if max_dd is not None:
        if max_dd < -0.30:
            score += 20
            factors.append(f"Large drawdown: {max_dd:.1%}")
        elif max_dd < -0.15:
            score += 10
            factors.append(f"Moderate drawdown: {max_dd:.1%}")
    
    # Sharpe ratio (risk-adjusted return)
    sharpe = volatility.get('sharpe_ratio')
    if sharpe is not None:
        if sharpe < 0:
            score += 15
            factors.append("Negative risk-adjusted returns")
        elif sharpe < 0.5:
            score += 5
            factors.append(f"Poor risk-adjusted returns (Sharpe: {sharpe:.2f})")
        elif sharpe > 1.5:
            score -= 10
            factors.append(f"Strong risk-adjusted returns (Sharpe: {sharpe:.2f})")
    
    # Clamp score
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "factors": factors,
        "assessment": "high" if score > 70 else "medium" if score > 30 else "low",
    }


def _collect_risk_factors(assessment: Dict[str, Any]) -> List[str]:
    """Collect all risk factors across categories."""
    factors = []
    
    for category in ["financial_risk", "market_risk", "volatility_risk"]:
        cat_data = assessment.get(category, {})
        factors.extend(cat_data.get("factors", []))
    
    return factors


def _collect_warnings(assessment: Dict[str, Any]) -> List[str]:
    """Collect high-priority warnings."""
    warnings = []
    
    # Financial warnings
    fin_risk = assessment.get("financial_risk", {})
    if fin_risk.get("assessment") == "high":
        warnings.append("High financial risk - Review leverage and liquidity")
    
    # Market warnings
    mkt_risk = assessment.get("market_risk", {})
    if mkt_risk.get("assessment") == "high":
        warnings.append("High market risk - Bearish trends detected")
    
    # Volatility warnings
    vol_risk = assessment.get("volatility_risk", {})
    if vol_risk.get("assessment") == "high":
        warnings.append("High volatility - Increased uncertainty")
    
    # Overall warning
    if assessment.get("overall_risk_score", 50) > 70:
        warnings.append("Overall risk profile is HIGH - Exercise caution")
    
    return warnings


# ── RISK METRICS FOR PORTFOLIO ───────────────────────────────────────────────

def calculate_var(returns: List[float], confidence: float = 0.95) -> Optional[float]:
    """
    Calculate Value at Risk (VaR) using historical method.
    
    Args:
        returns: List of returns
        confidence: Confidence level (e.g., 0.95 for 95% VaR)
        
    Returns:
        VaR as a positive percentage (e.g., 0.05 for 5% VaR)
    """
    if not returns:
        return None
    
    sorted_returns = sorted(returns)
    index = int((1 - confidence) * len(sorted_returns))
    var = -sorted_returns[index] if index < len(sorted_returns) else -sorted_returns[-1]
    
    return max(0, var)


def calculate_cvar(returns: List[float], confidence: float = 0.95) -> Optional[float]:
    """
    Calculate Conditional Value at Risk (CVaR / Expected Shortfall).
    """
    if not returns:
        return None
    
    sorted_returns = sorted(returns)
    index = int((1 - confidence) * len(sorted_returns))
    tail_returns = sorted_returns[:index]
    
    if tail_returns:
        return -sum(tail_returns) / len(tail_returns)
    return None