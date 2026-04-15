"""
Volatility calculations and risk metrics.
Pure functions - no side effects, no database.
"""

from typing import List, Optional, Dict, Any
import math
import logging

logger = logging.getLogger(__name__)

# Default risk-free rate (annualized) - India 10-year G-Sec ~7%
DEFAULT_RISK_FREE_RATE = 0.07


# ── BASIC VOLATILITY ─────────────────────────────────────────────────────────

def daily_returns(prices: List[float]) -> List[Optional[float]]:
    """
    Calculate daily percentage returns.
    Returns None for invalid transitions (e.g., zero/negative prices).
    """
    if len(prices) < 2:
        return []
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] is not None and prices[i-1] > 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        else:
            returns.append(None)  # Invalid price transition
    return returns


def historical_volatility(prices: List[float], window: int = 20, annualize: bool = True) -> List[Optional[float]]:
    """
    Calculate rolling historical volatility (standard deviation of returns).
    
    Args:
        prices: List of closing prices
        window: Rolling window size
        annualize: Whether to annualize (multiply by sqrt(252))
        
    Returns:
        List of volatility values (length matches input prices)
    """
    if not prices:
        return []
    
    returns = daily_returns(prices)
    
    if len(returns) < window:
        return [None] * len(prices)
    
    # First window-1 elements are None (not enough data)
    vol = [None] * (window - 1)
    
    for i in range(window - 1, len(returns)):
        window_returns = [r for r in returns[i - window + 1:i + 1] if r is not None]
        
        if len(window_returns) < 2:
            vol.append(None)
            continue
        
        mean_return = sum(window_returns) / len(window_returns)
        variance = sum((r - mean_return) ** 2 for r in window_returns) / (len(window_returns) - 1)
        std_dev = math.sqrt(variance)
        
        if annualize:
            std_dev *= math.sqrt(252)
        
        vol.append(std_dev)
    
    # Add one None at beginning to align with prices
    return [None] + vol


def current_volatility(prices: List[float], window: int = 20) -> Optional[float]:
    """Get current (most recent) volatility."""
    vol = historical_volatility(prices, window, annualize=True)
    if not vol:
        return None
    # Find the last non-None value
    for v in reversed(vol):
        if v is not None:
            return v
    return None


# ── VOLATILITY REGIMES ───────────────────────────────────────────────────────

def detect_volatility_regime(
    prices: List[float],
    window: int = 20,
    percentile_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Detect current volatility regime (low/normal/high).
    
    Returns:
        {
            "current_regime": "low"|"normal"|"high"|"unknown",
            "current_volatility": float,
            "volatility_percentile": float,
            "historical_vol_range": {"min": float, "max": float, "median": float}
        }
    """
    if not prices:
        return {"current_regime": "unknown", "current_volatility": None}
    
    vol_series = historical_volatility(prices, window, annualize=True)
    valid_vol = [v for v in vol_series if v is not None]
    
    if not valid_vol:
        return {"current_regime": "unknown", "current_volatility": None}
    
    current_vol = valid_vol[-1]
    sorted_vol = sorted(valid_vol)
    
    # Calculate percentile
    percentile = sum(1 for v in valid_vol if v <= current_vol) / len(valid_vol)
    
    # Determine regime
    if percentile > percentile_threshold:
        regime = "high"
    elif percentile < (1 - percentile_threshold):
        regime = "low"
    else:
        regime = "normal"
    
    return {
        "current_regime": regime,
        "current_volatility": current_vol,
        "volatility_percentile": percentile,
        "historical_vol_range": {
            "min": sorted_vol[0],
            "max": sorted_vol[-1],
            "median": sorted_vol[len(sorted_vol) // 2],
            "p25": sorted_vol[len(sorted_vol) // 4] if len(sorted_vol) >= 4 else None,
            "p75": sorted_vol[len(sorted_vol) * 3 // 4] if len(sorted_vol) >= 4 else None,
        }
    }


# ── MAX DRAWDOWN ─────────────────────────────────────────────────────────────

def calculate_max_drawdown(prices: List[float]) -> Optional[float]:
    """
    Calculate maximum drawdown (peak to trough decline).
    Returns as negative percentage (e.g., -0.25 for 25% drawdown).
    """
    if not prices or len(prices) < 2:
        return None
    
    # Find first valid price as initial peak
    peak = None
    for price in prices:
        if price is not None:
            peak = price
            break
    
    if peak is None:
        return None  # No valid prices
    
    max_dd = 0.0
    
    for price in prices:
        if price is None:
            continue
        if price > peak:
            peak = price
        if peak > 0:
            dd = (price - peak) / peak
            if dd < max_dd:
                max_dd = dd
    
    return max_dd

# ── COMPOSITE CALCULATION ────────────────────────────────────────────────────

def compute_all_volatility(
    prices: List[float],
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE
) -> Optional[Dict[str, Any]]:
    """
    Compute all volatility metrics from price data.
    
    Args:
        prices: List of closing prices (oldest → newest)
        risk_free_rate: Annualized risk-free rate for Sharpe ratio (default 7%)
        
    Returns:
        Dict with all volatility metrics, or None if insufficient data.
    """
    if not prices or len(prices) < 20:
        logger.warning(f"Insufficient price data for volatility: {len(prices) if prices else 0} points")
        return None
    
    volatility = {}
    
    # Basic volatility
    volatility['current_volatility_20d'] = current_volatility(prices, 20)
    volatility['current_volatility_60d'] = current_volatility(prices, 60) if len(prices) >= 60 else None
    
    # Volatility regime
    volatility['regime'] = detect_volatility_regime(prices)
    
    # Returns analysis
    returns = daily_returns(prices)
    valid_returns = [r for r in returns if r is not None]
    
    if valid_returns:
        volatility['avg_daily_return'] = sum(valid_returns) / len(valid_returns)
        volatility['positive_days_pct'] = sum(1 for r in valid_returns if r > 0) / len(valid_returns)
        volatility['negative_days_pct'] = sum(1 for r in valid_returns if r < 0) / len(valid_returns)
        
        # Annualized metrics
        volatility['annualized_return'] = volatility['avg_daily_return'] * 252
        
        # Calculate annualized volatility
        if len(valid_returns) > 1:
            variance = sum((r - volatility['avg_daily_return']) ** 2 for r in valid_returns) / (len(valid_returns) - 1)
            volatility['annualized_volatility'] = math.sqrt(variance) * math.sqrt(252)
        else:
            volatility['annualized_volatility'] = None
        
        # Sharpe ratio: (return - risk_free_rate) / volatility
        if volatility['annualized_volatility'] and volatility['annualized_volatility'] > 0:
            excess_return = volatility['annualized_return'] - risk_free_rate
            volatility['sharpe_ratio'] = excess_return / volatility['annualized_volatility']
        else:
            volatility['sharpe_ratio'] = None
        
        volatility['risk_free_rate_used'] = risk_free_rate
    else:
        volatility['avg_daily_return'] = None
        volatility['positive_days_pct'] = None
        volatility['negative_days_pct'] = None
        volatility['annualized_return'] = None
        volatility['annualized_volatility'] = None
        volatility['sharpe_ratio'] = None
        volatility['risk_free_rate_used'] = risk_free_rate
    
    # Max drawdown
    volatility['max_drawdown'] = calculate_max_drawdown(prices)
    
    return volatility


# ── OPTIONAL ADVANCED METRICS (Available but not in default profile) ─────────
# These functions are available for advanced use cases but not called by default.

def parkinson_volatility(high: List[float], low: List[float], window: int = 20) -> List[Optional[float]]:
    """
    Calculate Parkinson volatility (uses high-low range).
    More efficient than close-to-close volatility.
    """
    if len(high) < window or len(low) < window:
        return [None] * min(len(high), len(low))
    
    vol = [None] * (window - 1)
    
    for i in range(window - 1, len(high)):
        sum_sq = 0
        for j in range(i - window + 1, i + 1):
            if high[j] > 0 and low[j] > 0:
                hl_ratio = math.log(high[j] / low[j])
                sum_sq += hl_ratio ** 2
        
        parkinson = math.sqrt(sum_sq / (4 * window * math.log(2)))
        vol.append(parkinson * math.sqrt(252))
    
    return vol


def calculate_beta(
    stock_returns: List[float],
    market_returns: List[float],
    window: Optional[int] = None
) -> Optional[float]:
    """
    Calculate beta (systematic risk) relative to market.
    Beta = Covariance(stock, market) / Variance(market)
    """
    if window:
        stock_returns = stock_returns[-window:]
        market_returns = market_returns[-window:]
    
    # Filter out None values
    valid_pairs = [(s, m) for s, m in zip(stock_returns, market_returns) 
                   if s is not None and m is not None]
    
    if len(valid_pairs) < 2:
        return None
    
    stock_valid = [p[0] for p in valid_pairs]
    market_valid = [p[1] for p in valid_pairs]
    
    n = len(stock_valid)
    mean_stock = sum(stock_valid) / n
    mean_market = sum(market_valid) / n
    
    covariance = sum((stock_valid[i] - mean_stock) * (market_valid[i] - mean_market) for i in range(n)) / (n - 1)
    variance = sum((r - mean_market) ** 2 for r in market_valid) / (n - 1)
    
    return covariance / variance if variance != 0 else None