"""
Financial ratio calculations.
Pure functions - no side effects, no database.
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


# ── PROFITABILITY RATIOS ─────────────────────────────────────────────────────

def gross_margin(revenue: Optional[float], cogs: Optional[float]) -> Optional[float]:
    """Gross Profit / Revenue"""
    if revenue is None or cogs is None or revenue == 0:
        return None
    return (revenue - cogs) / revenue


def operating_margin(operating_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Operating Income / Revenue"""
    if operating_income is None or revenue is None or revenue == 0:
        return None
    return operating_income / revenue


def net_margin(net_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Net Income / Revenue"""
    if net_income is None or revenue is None or revenue == 0:
        return None
    return net_income / revenue


def return_on_equity(net_income: Optional[float], equity: Optional[float]) -> Optional[float]:
    """Net Income / Shareholder Equity"""
    if net_income is None or equity is None or equity == 0:
        return None
    return net_income / equity


def return_on_assets(net_income: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Net Income / Total Assets"""
    if net_income is None or total_assets is None or total_assets == 0:
        return None
    return net_income / total_assets


def return_on_invested_capital(nopat: Optional[float], invested_capital: Optional[float]) -> Optional[float]:
    """NOPAT / Invested Capital"""
    if nopat is None or invested_capital is None or invested_capital == 0:
        return None
    return nopat / invested_capital


# ── LIQUIDITY RATIOS ─────────────────────────────────────────────────────────

def current_ratio(current_assets: Optional[float], current_liabilities: Optional[float]) -> Optional[float]:
    """Current Assets / Current Liabilities"""
    if current_assets is None or current_liabilities is None or current_liabilities == 0:
        return None
    return current_assets / current_liabilities


def quick_ratio(
    current_assets: Optional[float], 
    inventory: Optional[float], 
    current_liabilities: Optional[float]
) -> Optional[float]:
    """(Current Assets - Inventory) / Current Liabilities"""
    if current_assets is None or inventory is None or current_liabilities is None or current_liabilities == 0:
        return None
    return (current_assets - inventory) / current_liabilities


def cash_ratio(cash: Optional[float], current_liabilities: Optional[float]) -> Optional[float]:
    """Cash / Current Liabilities"""
    if cash is None or current_liabilities is None or current_liabilities == 0:
        return None
    return cash / current_liabilities


# ── LEVERAGE RATIOS ──────────────────────────────────────────────────────────

def debt_to_equity(total_debt: Optional[float], total_equity: Optional[float]) -> Optional[float]:
    """Total Debt / Total Equity"""
    if total_debt is None or total_equity is None or total_equity == 0:
        return None
    return total_debt / total_equity


def debt_to_assets(total_debt: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Total Debt / Total Assets"""
    if total_debt is None or total_assets is None or total_assets == 0:
        return None
    return total_debt / total_assets


def interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
    """EBIT / Interest Expense"""
    if ebit is None or interest_expense is None or interest_expense == 0:
        return None
    return ebit / interest_expense


# ── EFFICIENCY RATIOS ────────────────────────────────────────────────────────

def asset_turnover(revenue: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Revenue / Total Assets"""
    if revenue is None or total_assets is None or total_assets == 0:
        return None
    return revenue / total_assets


def inventory_turnover(cogs: Optional[float], inventory: Optional[float]) -> Optional[float]:
    """COGS / Inventory"""
    if cogs is None or inventory is None or inventory == 0:
        return None
    return cogs / inventory


def receivables_turnover(revenue: Optional[float], accounts_receivable: Optional[float]) -> Optional[float]:
    """Revenue / Accounts Receivable"""
    if revenue is None or accounts_receivable is None or accounts_receivable == 0:
        return None
    return revenue / accounts_receivable


# ── VALUATION RATIOS ─────────────────────────────────────────────────────────

def earnings_per_share(net_income: Optional[float], shares_outstanding: Optional[float]) -> Optional[float]:
    """Net Income / Shares Outstanding"""
    if net_income is None or shares_outstanding is None or shares_outstanding == 0:
        return None
    return net_income / shares_outstanding


def price_to_earnings(price_per_share: Optional[float], eps: Optional[float]) -> Optional[float]:
    """Price Per Share / EPS"""
    if price_per_share is None or eps is None or eps == 0:
        return None
    return price_per_share / eps


def price_to_book(price_per_share: Optional[float], book_value_per_share: Optional[float]) -> Optional[float]:
    """Price Per Share / Book Value Per Share"""
    if price_per_share is None or book_value_per_share is None or book_value_per_share == 0:
        return None
    return price_per_share / book_value_per_share


def price_to_sales(market_cap: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Market Cap / Revenue"""
    if market_cap is None or revenue is None or revenue == 0:
        return None
    return market_cap / revenue


def dividend_yield(annual_dividend: Optional[float], price_per_share: Optional[float]) -> Optional[float]:
    """Annual Dividend / Price Per Share"""
    if annual_dividend is None or price_per_share is None or price_per_share == 0:
        return None
    return annual_dividend / price_per_share


# ── GROWTH RATIOS ────────────────────────────────────────────────────────────

def revenue_growth(current_revenue: Optional[float], prior_revenue: Optional[float]) -> Optional[float]:
    """(Current Revenue - Prior Revenue) / Prior Revenue"""
    if current_revenue is None or prior_revenue is None or prior_revenue == 0:
        return None
    return (current_revenue - prior_revenue) / prior_revenue


def earnings_growth(current_earnings: Optional[float], prior_earnings: Optional[float]) -> Optional[float]:
    """(Current Earnings - Prior Earnings) / Prior Earnings"""
    if current_earnings is None or prior_earnings is None or prior_earnings == 0:
        return None
    return (current_earnings - prior_earnings) / prior_earnings


# ── COMPOSITE CALCULATION ────────────────────────────────────────────────────

def compute_all_ratios(financials: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Compute all financial ratios from provided financial data."""
    if not financials:
        return None
    
    def get_val(key: str) -> Optional[float]:
        return financials.get(key)
    
    ratios = {}
    
    revenue = get_val('revenue')
    
    # Profitability
    ratios['gross_margin'] = gross_margin(revenue, get_val('cogs'))
    ratios['operating_margin'] = operating_margin(get_val('operating_income'), revenue)
    ratios['net_margin'] = net_margin(get_val('net_income'), revenue)
    ratios['return_on_equity'] = return_on_equity(get_val('net_income'), get_val('total_equity'))
    ratios['return_on_assets'] = return_on_assets(get_val('net_income'), get_val('total_assets'))
    
    # Liquidity
    ratios['current_ratio'] = current_ratio(get_val('current_assets'), get_val('current_liabilities'))
    ratios['quick_ratio'] = quick_ratio(
        get_val('current_assets'), 
        get_val('inventory'), 
        get_val('current_liabilities')
    )
    
    # Leverage
    ratios['debt_to_equity'] = debt_to_equity(get_val('total_debt'), get_val('total_equity'))
    ratios['interest_coverage'] = interest_coverage(get_val('ebit'), get_val('interest_expense'))
    
    # Growth
    ratios['revenue_growth'] = revenue_growth(revenue, get_val('prior_revenue'))
    ratios['earnings_growth'] = earnings_growth(get_val('net_income'), get_val('prior_net_income'))
    
    # Issue #6: Keep None values - don't strip them
    # Issue #14: Consistent key naming
    # Return all keys with None for missing values
    return ratios
