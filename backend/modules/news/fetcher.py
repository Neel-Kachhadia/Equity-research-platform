"""
News Fetcher — Livemint RSS (India business/economy, non-stock)
===============================================================
Source   : Livemint (livemint.com) — the only major Indian financial
           news site whose RSS feeds are publicly accessible (200 OK).

Moneycontrol and Business Standard both return 403 on their RSS URLs.
Economic Times RSS returns 200 but with 0 entries.

Filtering
---------
  URL-level  : drop article URLs that match stock/market path patterns
  Headline   : drop headlines mentioning stock/trading/Nifty/Sensex etc.
  Summary    : same keyword check on first 200 chars

Categories kept (Livemint sections)
------------------------------------
  companies, economy, technology, industry, news
  (politics is included but filtered for India-relevance by keyword)
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ── Working Livemint RSS feeds ────────────────────────────────────────────────
_LM_FEEDS: List[Dict[str, str]] = [
    {
        "url":      "https://www.livemint.com/rss/companies",
        "symbol":   "LM_COMPANIES",
        "name":     "Livemint Companies",
        "category": "companies",
    },
    {
        "url":      "https://www.livemint.com/rss/economy",
        "symbol":   "LM_ECONOMY",
        "name":     "Livemint Economy",
        "category": "economy",
    },
    {
        "url":      "https://www.livemint.com/rss/technology",
        "symbol":   "LM_TECH",
        "name":     "Livemint Technology",
        "category": "technology",
    },
    {
        "url":      "https://www.livemint.com/rss/industry",
        "symbol":   "LM_INDUSTRY",
        "name":     "Livemint Industry",
        "category": "industry",
    },
    {
        "url":      "https://www.livemint.com/rss/news",
        "symbol":   "LM_NEWS",
        "name":     "Livemint News",
        "category": "general",
    },
]

# ── Exclusion filters ──────────────────────────────────────────────────────────

_EXCLUDE_URL_PATTERNS = re.compile(
    r"""
    /stocks?/  |
    /stock-    |
    /share-price |
    /ipo/      |
    /ipo-      |
    /nifty     |
    /sensex    |
    /technicals|
    /technical-analysis |
    /trading/  |
    /futures   |
    /options/  |
    /commodit  |
    /mutual-fund |
    /portfolio-tracker |
    /markets/stocks
    """,
    re.VERBOSE | re.IGNORECASE,
)

_EXCLUDE_HEADLINE_KEYWORDS = re.compile(
    r"""
    \bstocks?\b   |
    \bshares?\b   |
    \bsensex\b    |
    \bnifty\b     |
    \bipo\b       |
    \bintraday\b  |
    \btrading\b   |
    \btarget\s+price\b |
    \bbuy\s+(now|call|signal)\b |
    \bsell\s+(signal|now|call)\b |
    \btechnical\s+view\b |
    \bmarket\s+update\b |
    \bfutures?\b  |
    \boptions?\b  |
    \bcommodit    |
    \bmutual\s+fund |
    \bfii\b       |
    \bdii\b       |
    \bfpo\b       |
    \bsme\s+ipo\b |
    \bnse\b       |
    \bbse\b       |
    \bsip\b
    """,
    re.VERBOSE | re.IGNORECASE,
)

# ── India-positive filter ──────────────────────────────────────────────────────
# Article MUST match at least one of these to be kept.
# Covers: country name, cities, major Indian companies, regulators, currency terms.
_INDIA_REQUIRED = re.compile(
    r"""
    \bindia(?:n)?\b          |   # India / Indian
    \bmumbai\b               |
    \bdelhi\b                |
    \bbengaluru\b            |
    \bbangalore\b            |
    \bhyderabad\b            |
    \bchennai\b              |
    \bpune\b                 |
    \bkolkata\b              |
    \bahmedabad\b            |
    # Indian regulators / institutions
    \brbi\b                  |   # Reserve Bank of India
    \bsebi\b                 |   # Securities & Exchange Board
    \bniti\s+aayog\b         |
    \bfinance\s+ministr      |
    \bunion\s+budget\b       |
    \bgst\b                  |   # Goods & Services Tax
    # Currency / size terms unique to India
    \brupee\b                |
    \bcrore\b                |
    \blakh\b                 |
    # Major Indian conglomerates / large-cap companies
    \btata\b                 |
    \breliance\b             |
    \binfosys\b              |
    \bwipro\b                |
    \bhcl\b                  |
    \badani\b                |
    \bmahindra\b             |
    \bhdfc\b                 |
    \bicici\b                |
    \baxis\s+bank\b          |
    \bsbi\b                  |   # State Bank of India
    \bkotak\b                |
    \bbajaj\b                |
    \bmaruti\b               |
    \bhero\s+moto\b          |
    \bltimindtree\b          |
    \btech\s+mahindra\b      |
    \bsun\s+pharma\b         |
    \bdr\s+reddy\b           |
    \bcipla\b                |
    \bzomato\b               |
    \bswiggy\b               |
    \bpaytm\b                |
    \bnykaa\b                |
    \bflipcart\b             |
    \bmeesho\b               |
    \bbyju\b                 |
    \bzepto\b                |
    \bindiab                 |   # IndiaBulls, IndiaMART etc.
    \bairtel\b               |
    \bjio\b                  |
    \bvodafone\s+idea\b      |
    \bntpc\b                 |
    \bcoal\s+india\b         |
    \bpower\s+grid\b         |
    \bhpcl\b                 |
    \bbpcl\b                 |
    \bioc\b                  |   # Indian Oil Corp
    \bgail\b                 |
    \bhal\b                  |   # Hindustan Aeronautics
    \bdivis\b                |
    \blasen\b                |   # L&T (Larsen & Toubro)
    \blarsen\b               |
    \bultratech\b            |
    \bgrасim\b               |
    \basian\s+paints\b       |
    \bhul\b                  |   # Hindustan Unilever
    \bnestl[eé]\s+india\b    |
    \bitc\b                  |
    \bdabur\b                |
    \bgodrej\b               |
    \bemaami\b               |
    \bmarico\b               |
    \bbritannia\b            |
    \binterglobe\b           |   # IndiGo parent
    \bindigo\b               |
    \bair\s+india\b          |
    \bspicejet\b
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _is_india_relevant(headline: str, summary: Optional[str]) -> bool:
    """Return True only if the article is about India / Indian companies."""
    text = headline + " " + (summary or "")
    return bool(_INDIA_REQUIRED.search(text))


# ── Corporate financial performance filter ────────────────────────────────────
# Articles must ALSO match this to be shown.
# Covers: quarterly results, earnings, P&L, revenue, business impact.
_CORP_PERFORMANCE = re.compile(
    r"""
    # Earnings / results
    \bquarterl                |   # quarterly
    \bq[1-4]\b               |   # Q1 Q2 Q3 Q4
    \b(fy|financial\s+year)\s*2\d |  # FY25 FY26
    \bearnings?\b            |
    \bresult[s]?\b           |
    \bprofit\b               |
    \bloss\b                 |
    \brevenue\b              |
    \bturnover\b             |
    \bebitda\b               |
    \bpat\b                  |   # Profit After Tax
    \bpbt\b                  |   # Profit Before Tax
    \bnet\s+income\b         |
    \boperating\s+profit\b   |
    \bgross\s+margin\b       |
    \bmargin[s]?\b           |
    # Business performance / impact
    \bguidance\b             |
    \boutlook\b              |
    \bgrowth\b               |
    \bdecline\b              |
    \bdrop[s]?\b             |
    \bjump[s]?\b             |
    \bsurge[s]?\b            |
    \bslump[s]?\b            |
    \bcontract[s]?\b         |
    \bexpand[s]?\b           |
    \bperformance\b          |
    \bforecast\b             |
    \bdowngrade\b            |
    \bupgrade\b              |
    \bimpact[s]?\b           |
    \baffect[s]?\b           |
    # P&L / financials
    \bbalance\s+sheet\b      |
    \bcash\s+flow\b          |
    \bdebt\b                 |
    \bleverage\b             |
    \binvestment\b           |
    \bacquisition\b          |
    \bmerger\b               |
    \bwrite-?off\b           |
    \bprovisioning\b         |
    \bvaluation\b            |
    \bfundraising\b          |
    \bfunding\b              |
    \b(?:announces?|reports?)\s+\d  # "announces 12% growth", "reports ₹500 cr"
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _is_corp_performance(headline: str, summary: Optional[str]) -> bool:
    """Return True if the article is about company financial/business performance."""
    text = headline + " " + (summary or "")
    return bool(_CORP_PERFORMANCE.search(text))



def _parse_rss_date(entry) -> Optional[datetime]:
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for field in ("published", "updated"):
        raw = getattr(entry, field, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass
    return None


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def _is_excluded_url(url: str) -> bool:
    return bool(_EXCLUDE_URL_PATTERNS.search(url))


def _is_excluded_text(text: str) -> bool:
    return bool(_EXCLUDE_HEADLINE_KEYWORDS.search(text))


# ── Core fetch ─────────────────────────────────────────────────────────────────

def _fetch_feed(feed: Dict[str, str], *, max_items: int = 50) -> List[Dict[str, Any]]:
    """Fetch and filter one RSS feed. Returns non-stock India business articles."""
    try:
        import feedparser
    except ImportError:
        logger.warning("[news] feedparser not installed — pip install feedparser")
        return []

    try:
        with httpx.Client(
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ErebusBot/1.0)"},
            follow_redirects=True,
        ) as client:
            resp = client.get(feed["url"])
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception as exc:
        logger.warning("[news] failed to fetch %s: %s", feed["url"], exc)
        return []

    articles: List[Dict[str, Any]] = []
    skipped = 0

    for entry in parsed.entries[:max_items]:
        url      = (getattr(entry, "link", None) or "").strip()
        headline = (getattr(entry, "title", None) or "").strip()

        if not url or not headline:
            continue
        if _is_excluded_url(url):
            skipped += 1
            continue
        if _is_excluded_text(headline):
            skipped += 1
            continue

        summary_raw = (
            getattr(entry, "summary", None)
            or getattr(entry, "description", None)
            or None
        )
        summary = _strip_html(summary_raw)[:500] if summary_raw else None
        if summary and _is_excluded_text(summary[:200]):
            skipped += 1
            continue

        # ── India-positive gate: must mention India/Indian companies ──
        if not _is_india_relevant(headline, summary):
            skipped += 1
            continue

        # ── Financial/corporate performance gate ──
        if not _is_corp_performance(headline, summary):
            skipped += 1
            continue

        articles.append({
            "company_symbol":      feed["symbol"],
            "company_name":        feed["name"],
            "headline":            headline,
            "summary":             summary,
            "source":              "livemint.com",
            "url":                 url,
            "image_url":           None,
            "published_at":        _parse_rss_date(entry),
            "provider":            "livemint_rss",
            "provider_article_id": url,
            "raw_payload":         None,
            "category":            feed.get("category", "general"),
            "country_tag":         "IN",
        })

    logger.info("[news] %s → kept %d / skipped %d", feed["name"], len(articles), skipped)
    return articles


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_all_india_news(max_per_feed: int = 50) -> List[Dict[str, Any]]:
    """Fetch all feeds, filter, deduplicate by URL."""
    all_articles: List[Dict] = []
    for feed in _LM_FEEDS:
        batch = _fetch_feed(feed, max_items=max_per_feed)
        all_articles.extend(batch)
        time.sleep(0.3)

    # Deduplicate by URL across feeds
    seen: set[str] = set()
    unique = [a for a in all_articles if not (a["url"] in seen or seen.add(a["url"]))]

    logger.info("[news] total after dedup: %d from %d feeds", len(unique), len(_LM_FEEDS))
    return unique


def seed_dashboard(upsert_fn: Callable) -> int:
    """Seed the news DB. Returns count of newly inserted articles."""
    logger.info("[news] seeding Livemint India business/economy feeds")
    articles = fetch_all_india_news(max_per_feed=50)
    if not articles:
        logger.error("[news] seed produced 0 articles — check network/feedparser")
        return 0
    inserted = upsert_fn(articles)
    logger.info("[news] seed complete → %d new articles", inserted)
    return inserted


# ── Backwards-compat stubs ────────────────────────────────────────────────────
def fetch_company_news(symbol: str, *, days_back: int = 30, force: bool = False):
    return []

def fetch_market_news(category: str = "general", count: int = 50):
    return []

fetch_all_rss = fetch_all_india_news
