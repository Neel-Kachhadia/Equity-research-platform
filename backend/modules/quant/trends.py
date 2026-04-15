"""
Price trend analysis and momentum indicators.
Pure functions - no side effects, no database.
"""

from typing import List, Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


# ── MOVING AVERAGES ──────────────────────────────────────────────────────────

def simple_moving_average(prices: List[float], window: int) -> List[Optional[float]]:
    """
    Calculate Simple Moving Average (SMA).
    Returns list of same length as input.
    
    Args:
        prices: List of closing prices
        window: Moving average window size
        
    Returns:
        List of SMA values (None for first window-1 elements)
    """
    if not prices:
        return []
    
    if len(prices) < window:
        logger.warning(f"Prices length ({len(prices)}) < window ({window})")
        return [None] * len(prices)
    
    sma = [None] * (window - 1)
    for i in range(window - 1, len(prices)):
        avg = sum(prices[i - window + 1:i + 1]) / window
        sma.append(avg)
    
    return sma


def exponential_moving_average(prices: List[float], window: int) -> List[Optional[float]]:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        prices: List of closing prices
        window: Moving average window size
        
    Returns:
        List of EMA values (None for first window-1 elements)
    """
    if not prices:
        return []
    
    if len(prices) < window:
        logger.warning(f"Prices length ({len(prices)}) < window ({window})")
        return [None] * len(prices)
    
    ema = [None] * (window - 1)
    multiplier = 2 / (window + 1)
    
    # First EMA is SMA
    first_ema = sum(prices[:window]) / window
    ema.append(first_ema)
    
    for i in range(window, len(prices)):
        current_ema = (prices[i] - ema[-1]) * multiplier + ema[-1]
        ema.append(current_ema)
    
    return ema


def moving_average_crossover(
    prices: List[float],
    short_window: int = 20,
    long_window: int = 50
) -> Dict[str, Any]:
    """
    Detect moving average crossovers (Golden Cross / Death Cross).
    
    Returns:
        {
            "short_ma": List[float],
            "long_ma": List[float],
            "crossover_signals": List[dict],
            "current_trend": "bullish"|"bearish"|"neutral"
        }
    """
    if not prices:
        return {
            "short_ma": [],
            "long_ma": [],
            "crossover_signals": [],
            "current_trend": "neutral"
        }
    
    short_ma = simple_moving_average(prices, short_window)
    long_ma = simple_moving_average(prices, long_window)
    
    signals = []
    current_trend = "neutral"
    
    # Find crossovers
    for i in range(1, len(prices)):
        if short_ma[i] is None or long_ma[i] is None:
            continue
        if short_ma[i-1] is None or long_ma[i-1] is None:
            continue
        
        # Golden Cross: short crosses above long
        if short_ma[i-1] <= long_ma[i-1] and short_ma[i] > long_ma[i]:
            signals.append({"index": i, "type": "golden"})
        
        # Death Cross: short crosses below long
        elif short_ma[i-1] >= long_ma[i-1] and short_ma[i] < long_ma[i]:
            signals.append({"index": i, "type": "death"})
    
    # Set current trend based on latest MA relationship
    if short_ma[-1] is not None and long_ma[-1] is not None:
        if short_ma[-1] > long_ma[-1]:
            current_trend = "bullish"
        elif short_ma[-1] < long_ma[-1]:
            current_trend = "bearish"
    
    return {
        "short_ma": short_ma,
        "long_ma": long_ma,
        "crossover_signals": signals,
        "current_trend": current_trend,
    }


# ── MOMENTUM INDICATORS ──────────────────────────────────────────────────────

def rate_of_change(prices: List[float], period: int = 10) -> List[Optional[float]]:
    """
    Calculate Rate of Change (ROC).
    ROC = ((Price - Price_n_periods_ago) / Price_n_periods_ago) * 100
    """
    if not prices or len(prices) <= period:
        return [None] * len(prices) if prices else []
    
    roc = [None] * period
    for i in range(period, len(prices)):
        if prices[i - period] != 0:
            change = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
            roc.append(change)
        else:
            roc.append(None)
    
    return roc


def relative_strength_index(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Calculate Relative Strength Index (RSI).
    RSI = 100 - (100 / (1 + RS))
    """
    if not prices or len(prices) < period + 1:
        return [None] * len(prices) if prices else []
    
    rsi = [None] * period
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    # First average
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        if avg_loss == 0:
            rs = 100
        else:
            rs = avg_gain / avg_loss
        rsi_value = 100 - (100 / (1 + rs))
        rsi.append(rsi_value)
        
        # Update averages
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    return rsi


def macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, List[Optional[float]]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Returns:
        {
            "macd_line": List[float],
            "signal_line": List[float],
            "histogram": List[float]
        }
    """
    if not prices:
        return {"macd_line": [], "signal_line": [], "histogram": []}
    
    ema_fast = exponential_moving_average(prices, fast)
    ema_slow = exponential_moving_average(prices, slow)
    
    macd_line = []
    for i in range(len(prices)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line.append(ema_fast[i] - ema_slow[i])
        else:
            macd_line.append(None)
    
    # Signal line is EMA of MACD line
    valid_macd = [v for v in macd_line if v is not None]
    if len(valid_macd) >= signal:
        signal_line_raw = exponential_moving_average(valid_macd, signal)
        pad_length = len(macd_line) - len(signal_line_raw)
        signal_line = [None] * pad_length + signal_line_raw
    else:
        signal_line = [None] * len(macd_line)
    
    # Histogram = MACD - Signal
    histogram = []
    for i in range(len(macd_line)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram.append(macd_line[i] - signal_line[i])
        else:
            histogram.append(None)
    
    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
    }


# ── TREND STRENGTH ───────────────────────────────────────────────────────────

def detect_support_resistance(
    prices: List[float],
    window: int = 20,
    threshold: float = 0.02
) -> Dict[str, List[float]]:
    """
    Detect support and resistance levels.
    
    Returns:
        {"support": List[float], "resistance": List[float]}
    """
    if not prices or len(prices) < window * 2:
        return {"support": [], "resistance": []}
    
    supports = []
    resistances = []
    
    for i in range(window, len(prices) - window):
        # Local minimum (support)
        is_support = True
        for j in range(1, window + 1):
            if prices[i] > prices[i - j]:
                is_support = False
                break
            if prices[i] > prices[i + j]:
                is_support = False
                break
        if is_support:
            supports.append(prices[i])
        
        # Local maximum (resistance)
        is_resistance = True
        for j in range(1, window + 1):
            if prices[i] < prices[i - j]:
                is_resistance = False
                break
            if prices[i] < prices[i + j]:
                is_resistance = False
                break
        if is_resistance:
            resistances.append(prices[i])
    
    # Cluster nearby levels
    def cluster_levels(levels: List[float]) -> List[float]:
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clustered.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
        
        clustered.append(sum(current_cluster) / len(current_cluster))
        return clustered
    
    return {
        "support": cluster_levels(supports),
        "resistance": cluster_levels(resistances),
    }


# ── COMPOSITE CALCULATION ────────────────────────────────────────────────────

def compute_all_trends(prices: List[float]) -> Optional[Dict[str, Any]]:
    """
    Compute all trend indicators from price data.
    
    Args:
        prices: List of closing prices (oldest → newest)
        
    Returns:
        Dict with all trend metrics, or None if insufficient data.
    """
    if not prices or len(prices) < 50:
        logger.warning(f"Insufficient price data: {len(prices) if prices else 0} points")
        return None
    
    trends = {}
    
    # Moving averages
    ma_crossover = moving_average_crossover(prices, 20, 50)
    trends['sma_20'] = simple_moving_average(prices, 20)
    trends['sma_50'] = simple_moving_average(prices, 50)
    trends['sma_200'] = simple_moving_average(prices, 200) if len(prices) >= 200 else None
    trends['current_trend'] = ma_crossover['current_trend']
    trends['crossover_signals'] = ma_crossover['crossover_signals'][-5:] if ma_crossover['crossover_signals'] else []
    
    # Momentum
    rsi_values = relative_strength_index(prices, 14)
    trends['rsi'] = rsi_values
    trends['current_rsi'] = rsi_values[-1] if rsi_values and rsi_values[-1] is not None else None
    
    roc_values = rate_of_change(prices, 10)
    trends['roc_10'] = roc_values
    trends['current_roc'] = roc_values[-1] if roc_values and roc_values[-1] is not None else None
    
    # MACD
    macd_data = macd(prices)
    trends['macd'] = {
        'line': macd_data['macd_line'][-1] if macd_data['macd_line'] else None,
        'signal': macd_data['signal_line'][-1] if macd_data['signal_line'] else None,
        'histogram': macd_data['histogram'][-1] if macd_data['histogram'] else None,
    }
    
    # Support/Resistance
    sr_levels = detect_support_resistance(prices)
    trends['support_levels'] = sr_levels['support'][-3:] if sr_levels['support'] else []
    trends['resistance_levels'] = sr_levels['resistance'][-3:] if sr_levels['resistance'] else []
    
    # Current price position
    current_price = prices[-1]
    if trends['sma_50'] and trends['sma_50'][-1] is not None:
        trends['price_vs_sma50'] = (current_price / trends['sma_50'][-1] - 1) * 100
    else:
        trends['price_vs_sma50'] = None
        
    if trends['sma_200'] and trends['sma_200'][-1] is not None:
        trends['price_vs_sma200'] = (current_price / trends['sma_200'][-1] - 1) * 100
    else:
        trends['price_vs_sma200'] = None
    
    # Trend strength summary
    trends['trend_strength'] = _assess_trend_strength(trends)
    
    return trends


def _assess_trend_strength(trends: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall trend strength from indicators."""
    strength = "neutral"
    score = 0
    
    # RSI assessment
    rsi = trends.get('current_rsi')
    if rsi is not None:
        if rsi > 70:
            score -= 1  # Overbought
        elif rsi < 30:
            score += 1  # Oversold
    
    # Price vs moving averages
    price_vs_sma50 = trends.get('price_vs_sma50')
    if price_vs_sma50 is not None:
        if price_vs_sma50 > 5:
            score += 1
        elif price_vs_sma50 < -5:
            score -= 1
    
    # MACD histogram
    macd = trends.get('macd', {})
    histogram = macd.get('histogram')
    if histogram is not None:
        if histogram > 0:
            score += 1
        elif histogram < 0:
            score -= 1
    
    if score > 1:
        strength = "bullish"
    elif score < -1:
        strength = "bearish"
    
    return {
        "assessment": strength,
        "score": score,
    }