"""
EREBUS · Yahoo Finance Scraper
===============================
Fetches price data and financial statements from Yahoo Finance.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import requests
import yfinance as yf

logger = logging.getLogger(__name__)


class YahooDataError(Exception):
    """Raised when Yahoo Finance data cannot be fetched."""
    pass


def fetch_yahoo_data(
    ticker: str,
    period: str = "5y",
    include_financials: bool = True,
) -> Dict[str, Any]:
    """
    Fetch price history and financial statements from Yahoo Finance.
    
    Args:
        ticker: Yahoo Finance ticker (e.g., "TCS.NS")
        period: Data period ("1y", "2y", "5y", "max")
        include_financials: Whether to fetch financial statements
        
    Returns:
        {
            "ticker": str,
            "prices": List[float],           # Close prices
            "dates": List[str],              # ISO format dates
            "volumes": List[int],            # Trading volumes
            "financials": Dict | None,       # Financial statements
            "info": Dict,                    # Company info
        }
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Price history
        hist = stock.history(period=period)
        if hist.empty:
            raise YahooDataError(f"No price data for {ticker}")
        
        prices = hist["Close"].tolist()
        dates = [d.strftime("%Y-%m-%d") for d in hist.index]
        volumes = hist["Volume"].tolist() if "Volume" in hist else []
        
        # Company info
        info = {
            "name": stock.info.get("longName", ticker),
            "sector": stock.info.get("sector", "Unknown"),
            "industry": stock.info.get("industry", "Unknown"),
            "market_cap": stock.info.get("marketCap"),
            "currency": stock.info.get("currency", "INR"),
        }
        
        result = {
            "ticker": ticker,
            "prices": prices,
            "dates": dates,
            "volumes": volumes,
            "info": info,
            "financials": None,
        }
        
        # Financial statements
        if include_financials:
            result["financials"] = _fetch_financials(stock)
        
        logger.info("[Yahoo] Fetched %s: %d prices, financials=%s", 
                   ticker, len(prices), include_financials)
        
        return result
        
    except Exception as e:
        logger.error("[Yahoo] Failed for %s: %s", ticker, e)
        raise YahooDataError(f"Failed to fetch {ticker}: {e}") from e


def _fetch_financials(stock: yf.Ticker) -> Dict[str, Any]:
    """Extract financial statements from yfinance Ticker."""
    try:
        # Income Statement
        income = stock.financials
        income_dict = {}
        if not income.empty:
            latest = income.iloc[:, 0]
            income_dict = {
                "revenue": _safe_float(latest.get("Total Revenue")),
                "net_income": _safe_float(latest.get("Net Income")),
                "operating_income": _safe_float(latest.get("Operating Income")),
                "ebit": _safe_float(latest.get("EBIT")),
                "interest_expense": _safe_float(latest.get("Interest Expense")),
                "tax": _safe_float(latest.get("Tax Provision")),
                "eps": _safe_float(latest.get("Basic EPS")),
            }
        
        # Balance Sheet
        balance = stock.balance_sheet
        balance_dict = {}
        if not balance.empty:
            latest = balance.iloc[:, 0]
            balance_dict = {
                "total_assets": _safe_float(latest.get("Total Assets")),
                "total_equity": _safe_float(latest.get("Total Equity Gross Minority Interest")),
                "total_debt": _safe_float(latest.get("Total Debt")),
                "current_assets": _safe_float(latest.get("Current Assets")),
                "current_liabilities": _safe_float(latest.get("Current Liabilities")),
                "inventory": _safe_float(latest.get("Inventory")),
                "cash": _safe_float(latest.get("Cash And Cash Equivalents")),
            }
        
        # Cash Flow
        cashflow = stock.cashflow
        cashflow_dict = {}
        if not cashflow.empty:
            latest = cashflow.iloc[:, 0]
            cashflow_dict = {
                "cfo": _safe_float(latest.get("Operating Cash Flow")),
                "cfi": _safe_float(latest.get("Investing Cash Flow")),
                "cff": _safe_float(latest.get("Financing Cash Flow")),
                "capex": _safe_float(latest.get("Capital Expenditure")),
                "fcf": _safe_float(latest.get("Free Cash Flow")),
            }
        
        return {
            "income": income_dict,
            "balance": balance_dict,
            "cashflow": cashflow_dict,
            "as_of": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.warning("[Yahoo] Financials fetch failed: %s", e)
        return None


def _safe_float(value) -> Optional[float]:
    """Convert to float safely, return None if invalid."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_multiple_companies(
    tickers: List[str],
    period: str = "5y",
) -> Dict[str, Any]:
    """
    Fetch data for multiple companies.
    
    Returns:
        Dict mapping ticker -> data dict
    """
    results = {}
    errors = {}
    
    for ticker in tickers:
        try:
            results[ticker] = fetch_yahoo_data(ticker, period)
            logger.info("[Yahoo] [OK] %s", ticker)
        except YahooDataError as e:
            errors[ticker] = str(e)
            logger.error("[Yahoo] [FAIL] %s: %s", ticker, e)
    
    return {
        "success": results,
        "errors": errors,
        "total": len(tickers),
        "successful": len(results),
    }