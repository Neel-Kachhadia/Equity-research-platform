"""
EREBUS — Financial Schema Normalizer
=====================================
Maps arbitrary column/row names from any Excel format to a standard schema
using keyword-group matching.  No external libraries.  Deterministic.

[Documentation unchanged - kept for brevity]
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

# ── Required output fields with safe defaults ──────────────────────────────────

REQUIRED_FIELDS: Dict[str, float] = {
    "revenue":               0.0,
    "net_income":            0.0,
    "operating_profit":      0.0,
    "expenses":              0.0,
    "other_income":          0.0,
    "depreciation":          0.0,
    "interest_expense":      0.0,
    "tax":                   0.0,
    "pbt":                   0.0,
    "eps":                   0.0,
    "total_equity":          1.0,   # never 0 — used as denominator
    "reserves":              0.0,
    "equity_capital":        0.0,
    "borrowings":            0.0,
    "total_assets":          0.0,
    "current_assets":        0.0,
    "current_liabilities":   0.0,
    "inventory":             0.0,
    "investments":           0.0,
    "other_liabilities":     0.0,
    "cash_from_operations":  0.0,
    "cash_from_investing":   0.0,
    "cash_from_financing":   0.0,
    "capex":                 0.0,
    "fcf":                   0.0,
}

# Fields that can legitimately be zero (no default override warning needed)
_ZERO_OK_FIELDS = {"borrowings", "interest_expense", "tax", "capex", "other_income", "investments"}

# ── Keyword groups ─────────────────────────────────────────────────────────────
# [KEYWORD_GROUPS unchanged - kept for brevity]
_KEYWORD_GROUPS: List[tuple] = [
    # Revenue
    ("revenue",          10,  ["total", "revenue"],            ["net", "other", "segment"]),
    ("revenue",          11,  ["net", "revenue"],              ["profit", "other"]),
    ("revenue",          12,  ["sales"],                        ["cost", "other"]),
    ("revenue",          13,  ["revenue"],                      ["operating", "profit", "finance", "other", "segment"]),
    ("revenue",          14,  ["income", "operation"],         ["other", "finance", "investing"]),
    ("revenue",          15,  ["turnover"],                    ["cost"]),
    
    # Net Income
    ("net_income",       20,  ["profit", "after", "tax"],      ["before", "ation", "attributable"]),
    ("net_income",       21,  ["net", "profit"],               ["before", "operating", "gross"]),
    ("net_income",       22,  ["net", "income"],               ["operating", "other", "before", "gross"]),
    ("net_income",       23,  ["pat"],                         []),
    ("net_income",       24,  ["earnings"],                    ["before", "per", "basic", "dilut"]),
    
    # Operating Profit / EBIT
    ("operating_profit", 30,  ["operating", "profit"],         ["before", "interest", "after"]),
    ("operating_profit", 31,  ["ebit"],                        ["da", "margin"]),
    ("operating_profit", 32,  ["pbdit"],                       []),
    ("operating_profit", 33,  ["pbit"],                        []),
    
    # Expenses
    ("expenses",         40,  ["total", "expense"],            ["other", "finance", "deprec"]),
    ("expenses",         41,  ["total", "cost"],               ["revenue", "of", "employee", "deprec"]),
    ("expenses",         42,  ["operating", "expense"],        ["other"]),
    ("expenses",         43,  ["cost", "revenue"],             ["net", "total", "other"]),
    
    # Other Income
    ("other_income",     50,  ["other", "income"],             ["comprehensive", "total"]),
    ("other_income",     51,  ["finance", "income"],           []),
    ("other_income",     52,  ["non", "operating", "income"],  []),
    
    # Depreciation
    ("depreciation",     60,  ["depreciation"],                []),
    ("depreciation",     61,  ["amortisation"],               []),
    ("depreciation",     62,  ["amortization"],               []),
    ("depreciation",     63,  ["d&a"],                        []),
    ("depreciation",     64,  ["dna"],                        []),
    
    # Interest Expense
    ("interest_expense", 70,  ["interest", "expense"],        ["income", "income"]),
    ("interest_expense", 71,  ["finance", "cost"],             []),
    ("interest_expense", 72,  ["interest", "paid"],            []),
    ("interest_expense", 73,  ["borrowing", "cost"],           []),
    
    # Tax
    ("tax",              80,  ["tax", "expense"],              []),
    ("tax",              81,  ["provision", "tax"],            []),
    ("tax",              82,  ["income", "tax"],               ["before", "net"]),
    
    # Profit Before Tax
    ("pbt",              90,  ["profit", "before", "tax"],     []),
    ("pbt",              91,  ["income", "before", "tax"],     []),
    ("pbt",              92,  ["pbt"],                         []),
    ("pbt",              93,  ["ebt"],                         []),
    
    # EPS
    ("eps",             100,  ["earning", "per", "share"],     []),
    ("eps",             101,  ["eps"],                         ["growth"]),
    ("eps",             102,  ["basic", "eps"],                []),
    ("eps",             103,  ["diluted", "eps"],              []),
    
    # Balance Sheet: Equity
    ("equity_capital",  110,  ["equity", "share", "capital"],  ["reserve", "total"]),
    ("equity_capital",  111,  ["share", "capital"],            ["reserve", "total", "working"]),
    ("equity_capital",  112,  ["paid", "capital"],             []),
    
    ("reserves",        120,  ["reserve"],                     ["capital", "total"]),
    ("reserves",        121,  ["surplus"],                     []),
    ("reserves",        122,  ["retained", "earning"],         []),
    
    ("total_equity",    130,  ["total", "equity"],             ["fund", "capital", "return"]),
    ("total_equity",    131,  ["shareholder", "equity"],      []),
    ("total_equity",    132,  ["stockholder", "equity"],      []),
    ("total_equity",    133,  ["net", "worth"],                []),
    
    # Balance Sheet: Debt
    ("borrowings",      140,  ["borrowing"],                   ["cost"]),
    ("borrowings",      141,  ["total", "debt"],               ["net"]),
    ("borrowings",      142,  ["long", "term", "debt"],        []),
    ("borrowings",      143,  ["short", "term", "debt"],       []),
    ("borrowings",      144,  ["loan"],                        ["net", "given"]),
    
    ("other_liabilities", 150, ["other", "liabilit"],         ["current"]),
    ("other_liabilities", 151, ["deferred", "liabilit"],      []),
    
    ("current_liabilities", 160, ["current", "liabilit"],     ["other"]),
    ("current_liabilities", 161, ["total", "current", "liab"], []),
    
    # Balance Sheet: Assets
    ("total_assets",    170,  ["total", "asset"],              ["current", "net", "tangible"]),
    ("total_assets",    171,  ["total", "liabilit", "equity"], []),
    
    ("current_assets",  180,  ["current", "asset"],           ["other", "non"]),
    ("current_assets",  181,  ["total", "current", "asset"],  []),
    
    ("inventory",       190,  ["inventor"],                    []),
    ("inventory",       191,  ["stock"],                       ["market", "equity", "option", "buy"]),
    
    ("investments",     200,  ["investment"],                  ["return", "income"]),
    
    # Cash Flow
    ("cash_from_operations", 210, ["operating", "activit"],   []),
    ("cash_from_operations", 211, ["cash", "operation"],      []),
    ("cash_from_operations", 212, ["cfo"],                    []),
    
    ("cash_from_investing",  220, ["investing", "activit"],   []),
    ("cash_from_investing",  221, ["cash", "invest"],         ["return"]),
    ("cash_from_investing",  222, ["cfi"],                    []),
    
    ("cash_from_financing",  230, ["financing", "activit"],   []),
    ("cash_from_financing",  231, ["cash", "financ"],         []),
    ("cash_from_financing",  232, ["cff"],                    []),
    
    ("capex",           240,  ["capital", "expenditure"],     []),
    ("capex",           241,  ["capex"],                       []),
    ("capex",           242,  ["purchase", "asset"],          ["financial"]),
    ("capex",           243,  ["addition", "asset"],          ["financial"]),
    
    ("fcf",             250,  ["free", "cash", "flow"],        []),
    ("fcf",             251,  ["fcf"],                         []),
]

_KEYWORD_GROUPS.sort(key=lambda x: x[1])


# ── Step 1: clean_key ──────────────────────────────────────────────────────────

def clean_key(raw: str) -> str:
    """
    Normalize a raw column/narration string for matching:
    - lowercase
    - remove special characters and extra whitespace
    - keep alphanumeric and spaces only

    Examples:
        "Net Profit (after tax)"  -> "net profit after tax"
        "profit_after_tax"        -> "profit after tax"
        "Cash from Ops."          -> "cash from ops"
        "  EBITDA  "              -> "ebitda"
    """
    if not raw:
        return ""
    s = raw.lower()
    s = re.sub(r"[_\-/\\.()\[\]{}]", " ", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ── Step 2: match_key ─────────────────────────────────────────────────────────

def match_key(raw: str) -> Optional[str]:
    """
    Map a raw narration/column name to a standard schema key.
    Uses word-boundary matching to prevent false positives.
    """
    cleaned = clean_key(raw)
    if not cleaned:
        return None
    
    # Split into words for exact matching
    words = set(cleaned.split())
    
    for std_key, _priority, must_have, must_not_have in _KEYWORD_GROUPS:
        # All mandatory keywords must be present as whole words
        # (not substrings to avoid "tax" matching "taxation")
        must_have_ok = True
        for mh in must_have:
            # Check if any word contains the mandatory keyword as a whole word
            found = False
            for word in words:
                # Exact match or word starts/ends with the keyword
                if word == mh or word.startswith(mh + " ") or word.endswith(" " + mh):
                    found = True
                    break
                # Also check if the cleaned string contains the phrase
                if f" {mh} " in f" {cleaned} ":
                    found = True
                    break
            if not found:
                must_have_ok = False
                break
        
        if not must_have_ok:
            continue
        
        # No forbidden keywords may be present as whole words
        must_not_have_ok = True
        for mnh in must_not_have:
            for word in words:
                if word == mnh:
                    must_not_have_ok = False
                    break
            if f" {mnh} " in f" {cleaned} ":
                must_not_have_ok = False
                break
            if not must_not_have_ok:
                break
        
        if must_not_have_ok:
            return std_key
    
    return None
    

# ── Step 3: normalize_financials ──────────────────────────────────────────────

def normalize_financials(
    rows: Sequence[Dict[str, Any]],
    *,
    value_key: str = "values",
    narration_key: str = "narration",
) -> Dict[str, float]:
    """
    Convert a list of {narration: str, values: List[float|None]} rows
    into a flat standard financials dict using the most recent non-None value.
    """
    result: Dict[str, float] = {}
    seen_values: Dict[str, List[float]] = {}  # Track all values per field for debugging
    unmatched: List[str] = []

    for row in rows:
        narration = row.get(narration_key, "")
        values    = row.get(value_key, [])

        std_key = match_key(narration)

        if std_key is None:
            unmatched.append(narration)
            continue

        # Extract the most recent valid (non-None) value
        latest = _last_valid(values)
        if latest is not None:
            # Prefer the first occurrence (usually from primary sheet)
            if std_key not in result:
                result[std_key] = latest
                seen_values[std_key] = [latest]
            else:
                seen_values[std_key].append(latest)

    if unmatched:
        logger.debug("[normalizer] Unmatched narrations (%d): %s", len(unmatched), unmatched[:10])

    # Apply defaults for missing fields
    for field, default in REQUIRED_FIELDS.items():
        if field not in result:
            # Only warn if it's not a zero-ok field or if we have other data
            if field not in _ZERO_OK_FIELDS or len(result) > 5:
                logger.warning("[normalizer] Required field '%s' missing — using default %.1f", field, default)
            result[field] = default

    _apply_derived_fields(result)

    return result


# ── Internal helpers ──────────────────────────────────────────────────────────

def _last_valid(values: Sequence) -> Optional[float]:
    """
    Return the last non-None numeric value (including zero).
    Zero is a valid financial value (e.g., zero debt).
    """
    for v in reversed(values):
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _apply_derived_fields(fin: Dict[str, float]) -> None:
    """
    Compute missing high-level fields from available data.
    All mutations are in-place.
    """
    # total_equity = equity_capital + reserves
    if fin["total_equity"] <= 1.0 and (fin["equity_capital"] + fin["reserves"]) > 0:
        fin["total_equity"] = fin["equity_capital"] + fin["reserves"]

    # operating_profit = revenue - expenses - depreciation
    if fin["operating_profit"] == 0.0 and fin["revenue"] > 0.0:
        candidate = fin["revenue"] - fin["expenses"] - fin["depreciation"]
        fin["operating_profit"] = candidate  # Allow negative values

    # fcf = cash_from_operations - capex
    if fin["fcf"] == 0.0 and fin["cash_from_operations"] != 0.0:
        fin["fcf"] = fin["cash_from_operations"] - abs(fin["capex"])

    # pbt = net_income + tax (if pbt missing but components available)
    if fin["pbt"] == 0.0 and fin["net_income"] != 0.0 and fin["tax"] != 0.0:
        fin["pbt"] = fin["net_income"] + fin["tax"]

    # Ensure total_equity is never exactly 0
    if fin["total_equity"] == 0.0:
        fin["total_equity"] = 1.0


# ── Convenience: build full financials dict from CompanyContext sheets ─────────

def build_financials_from_sheets(sheets: Dict[str, Any]) -> Dict[str, float]:
    """
    Convenience wrapper: takes the `sheets` dict and returns normalized financials.
    """
    all_rows: List[Dict[str, Any]] = []
    for sheet_data in sheets.values():
        all_rows.extend(sheet_data.get("rows", []))

    return normalize_financials(all_rows)


# ── Validation helper ─────────────────────────────────────────────────────────

def validate_financials(fin: Dict[str, float]) -> List[str]:
    """
    Check financials dict for consistency issues.
    Returns list of warning messages.
    """
    warnings = []
    
    # Accounting identity: Assets = Liabilities + Equity
    assets = fin["total_assets"]
    liab_equity = fin["current_liabilities"] + fin["other_liabilities"] + fin["borrowings"] + fin["total_equity"]
    if assets > 0 and abs(assets - liab_equity) / assets > 0.2:  # 20% tolerance
        warnings.append(f"Balance sheet mismatch: Assets={assets:.1f}, L+E={liab_equity:.1f}")
    
    # P&L consistency
    if fin["revenue"] > 0 and fin["net_income"] > fin["revenue"]:
        warnings.append(f"Net income ({fin['net_income']:.1f}) exceeds revenue ({fin['revenue']:.1f})")
    
    # Cash flow consistency
    if fin["fcf"] != 0 and fin["cash_from_operations"] == 0:
        warnings.append("FCF present but operating cash flow missing")
    
    return warnings