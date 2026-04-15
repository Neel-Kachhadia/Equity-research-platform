"""
News DB helpers
===============
Creates and queries the company_news table.
Uses the existing psycopg2 pool — no ORM overhead.

v2 changes
----------
* Added `category` and `country_tag` columns (ALTER IF NOT EXISTS — safe to run repeatedly).
* get_dashboard_news() now filters to Moneycontrol India-only non-stock articles.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.database import execute_query, execute_single, get_cursor

logger = logging.getLogger(__name__)

# ── Table DDL ─────────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS company_news (
    id                  SERIAL PRIMARY KEY,
    company_symbol      VARCHAR(50)  NOT NULL,
    company_name        VARCHAR(255),
    headline            TEXT         NOT NULL,
    summary             TEXT,
    source              VARCHAR(255),
    url                 TEXT,
    image_url           TEXT,
    published_at        TIMESTAMP,
    fetched_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    provider            VARCHAR(50)  NOT NULL DEFAULT 'rss',
    provider_article_id VARCHAR(255),
    raw_payload         JSONB,
    category            VARCHAR(100),
    country_tag         VARCHAR(10)  DEFAULT 'IN',
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_company_news_url UNIQUE (url)
)
"""

# Safe migrations — add columns only if they don't exist yet
_MIGRATIONS = [
    """
    DO $$ BEGIN
        ALTER TABLE company_news ADD COLUMN category VARCHAR(100);
    EXCEPTION WHEN duplicate_column THEN NULL; END $$
    """,
    """
    DO $$ BEGIN
        ALTER TABLE company_news ADD COLUMN country_tag VARCHAR(10) DEFAULT 'IN';
    EXCEPTION WHEN duplicate_column THEN NULL; END $$
    """,
]

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_cn_symbol     ON company_news(company_symbol)",
    "CREATE INDEX IF NOT EXISTS idx_cn_published  ON company_news(published_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_cn_source     ON company_news(source)",
    "CREATE INDEX IF NOT EXISTS idx_cn_fetched    ON company_news(fetched_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_cn_category   ON company_news(category)",
    "CREATE INDEX IF NOT EXISTS idx_cn_country    ON company_news(country_tag)",
]

_DB_READY = False


def ensure_table() -> bool:
    """
    Idempotent DDL — creates table + indexes if they don't exist,
    runs safe column migrations.
    Returns True on success, False if DB is unreachable.
    """
    global _DB_READY
    if _DB_READY:
        return True
    try:
        with get_cursor() as cur:
            cur.execute(_CREATE_TABLE)
            for migration in _MIGRATIONS:
                cur.execute(migration)
            for idx in _INDEXES:
                cur.execute(idx)
        _DB_READY = True
        logger.info("company_news table ready (v2)")
        return True
    except Exception as exc:
        logger.warning("company_news table not ready: %s", exc)
        _DB_READY = False
        return False


# ── Write helpers ─────────────────────────────────────────────────────────────

def upsert_articles(articles: List[Dict[str, Any]]) -> int:
    """
    Insert new articles; skip duplicates via ON CONFLICT (url) DO NOTHING.
    Returns the count of rows actually inserted.
    """
    if not articles:
        return 0
    inserted = 0
    with get_cursor() as cur:
        for a in articles:
            cur.execute(
                """
                INSERT INTO company_news
                    (company_symbol, company_name, headline, summary,
                     source, url, image_url, published_at,
                     provider, provider_article_id, raw_payload,
                     category, country_tag)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO NOTHING
                """,
                (
                    a.get("company_symbol"),
                    a.get("company_name"),
                    a.get("headline", ""),
                    a.get("summary"),
                    a.get("source"),
                    a.get("url"),
                    a.get("image_url"),
                    a.get("published_at"),
                    a.get("provider", "moneycontrol_rss"),
                    a.get("provider_article_id"),
                    json.dumps(a.get("raw_payload")) if a.get("raw_payload") else None,
                    a.get("category"),
                    a.get("country_tag", "IN"),
                ),
            )
            if cur.rowcount:
                inserted += 1
    return inserted


# ── Read helpers ──────────────────────────────────────────────────────────────

def _row_to_dict(row: Dict) -> Dict:
    """Serialise a DB row to a JSON-safe dict."""
    return {
        "id":             row["id"],
        "company_symbol": row["company_symbol"],
        "company_name":   row["company_name"],
        "headline":       row["headline"],
        "summary":        row["summary"],
        "source":         row["source"],
        "url":            row["url"],
        "image_url":      row["image_url"],
        "published_at":   row["published_at"].isoformat() if row["published_at"] else None,
        "fetched_at":     row["fetched_at"].isoformat()   if row["fetched_at"]   else None,
        "provider":       row["provider"],
        "category":       row.get("category"),
        "country_tag":    row.get("country_tag", "IN"),
    }


def get_latest_for_symbol(symbol: str, limit: int = 10) -> List[Dict]:
    rows = execute_query(
        """
        SELECT id, company_symbol, company_name, headline, summary,
               source, url, image_url, published_at, fetched_at,
               provider, category, country_tag
        FROM   company_news
        WHERE  company_symbol = %s
        ORDER  BY published_at DESC NULLS LAST
        LIMIT  %s
        """,
        (symbol.upper(), limit),
    )
    return [_row_to_dict(r) for r in rows]


def get_dashboard_news(limit: int = 10) -> List[Dict]:
    """
    Return latest India-only, non-stock news articles.
    Accepts articles from livemint_rss or moneycontrol_rss providers.
    Sorted by published_at DESC.
    """
    rows = execute_query(
        """
        SELECT id, company_symbol, company_name, headline, summary,
               source, url, image_url, published_at, fetched_at,
               provider, category, country_tag
        FROM   company_news
        WHERE  (country_tag = 'IN' OR country_tag IS NULL)
          AND  (provider LIKE 'livemint%%' OR provider LIKE 'moneycontrol%%')
        ORDER  BY published_at DESC NULLS LAST
        LIMIT  %s
        """,
        (limit,),
    )
    return [_row_to_dict(r) for r in rows]



def get_history_for_symbol(
    symbol: str, limit: int = 20, offset: int = 0
) -> Dict[str, Any]:
    rows = execute_query(
        """
        SELECT id, company_symbol, company_name, headline, summary,
               source, url, image_url, published_at, fetched_at,
               provider, category, country_tag
        FROM   company_news
        WHERE  company_symbol = %s
        ORDER  BY published_at DESC NULLS LAST
        LIMIT  %s OFFSET %s
        """,
        (symbol.upper(), limit, offset),
    )
    total_row = execute_single(
        "SELECT COUNT(*) AS n FROM company_news WHERE company_symbol = %s",
        (symbol.upper(),),
    )
    return {
        "articles": [_row_to_dict(r) for r in rows],
        "total":    total_row["n"] if total_row else 0,
        "limit":    limit,
        "offset":   offset,
    }
