"""
News Router — FastAPI endpoints
================================
GET  /dashboard/news       → top-10 Moneycontrol India business/economy news
POST /news/seed            → manually re-seed from Moneycontrol

Legacy endpoints (kept for compatibility, return [] gracefully):
GET  /news/{symbol}
POST /news/{symbol}/refresh
GET  /news/{symbol}/history
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from modules.news.db import (
    ensure_table,
    upsert_articles,
    get_latest_for_symbol,
    get_dashboard_news,
    get_history_for_symbol,
)
from modules.news.fetcher import seed_dashboard

logger = logging.getLogger(__name__)

router           = APIRouter(prefix="/news", tags=["News"])
dashboard_router = APIRouter(tags=["News"])

# ── DB init guard ─────────────────────────────────────────────────────────────

_DB_READY = False
_SEEDED   = False


def _require_db():
    global _DB_READY
    if not _DB_READY:
        _DB_READY = ensure_table()
    if not _DB_READY:
        raise HTTPException(
            status_code=503,
            detail=(
                "News database not available. "
                "Check that PostgreSQL is reachable and port 5432 is whitelisted."
            ),
        )


# Attempt table creation at import (non-fatal if DB is offline)
try:
    ensure_table()
    _DB_READY = True
except Exception:
    pass


# ── Seed endpoint ─────────────────────────────────────────────────────────────

@router.get("/seed", include_in_schema=False)
@router.post("/seed", summary="Seed India news from Moneycontrol")
def trigger_seed():
    """Manually trigger Moneycontrol news seeding."""
    _require_db()
    global _SEEDED
    inserted = seed_dashboard(upsert_articles)
    _SEEDED = inserted > 0
    return {"seeded": inserted, "source": "moneycontrol"}


# ── Legacy company-news endpoints (no-op — kept for compatibility) ─────────────

@router.get("/{symbol}", summary="Latest news for a company (legacy)")
def get_news(
    symbol: str,
    limit:   int  = Query(10, ge=1, le=50),
    refresh: bool = Query(False),
):
    _require_db()
    return {
        "symbol":   symbol.upper(),
        "articles": get_latest_for_symbol(symbol.upper(), limit=limit),
    }


@router.post("/{symbol}/refresh", summary="Force-fetch news for company (legacy)")
def refresh_news(symbol: str):
    _require_db()
    return {"symbol": symbol.upper(), "fetched": 0, "inserted": 0}


@router.get("/{symbol}/history", summary="Paginated news history")
def get_news_history(
    symbol: str,
    limit:  int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    _require_db()
    return get_history_for_symbol(symbol.upper(), limit=limit, offset=offset)


# ── Dashboard endpoint ────────────────────────────────────────────────────────

@dashboard_router.get(
    "/dashboard/news",
    summary="Latest India business/economy news from Moneycontrol",
)
def get_dashboard_news_endpoint(
    limit:            int             = Query(10, ge=1, le=50),
    refresh:          bool            = Query(False, description="Re-fetch from Moneycontrol"),
    background_tasks: BackgroundTasks = None,
):
    """
    Returns the latest *limit* India business/economy articles from Moneycontrol.

    Auto-seed on first empty load.
    Pass `refresh=true` to trigger a background re-fetch.
    """
    _require_db()
    global _SEEDED

    items = get_dashboard_news(limit=limit)

    # Auto-seed on first empty load
    if not items and not _SEEDED:
        logger.info("[news/dashboard] no articles — seeding Moneycontrol feeds")
        try:
            inserted = seed_dashboard(upsert_articles)
            _SEEDED = inserted > 0
            if inserted:
                items = get_dashboard_news(limit=limit)
        except Exception as exc:
            logger.error("[news/dashboard] seed failed: %s", exc)

    # Explicit background refresh
    elif refresh:
        if background_tasks:
            background_tasks.add_task(_background_refresh)
        else:
            _background_refresh()

    return {"articles": items, "total": len(items), "source": "moneycontrol"}


def _background_refresh():
    global _SEEDED
    try:
        inserted = seed_dashboard(upsert_articles)
        _SEEDED = inserted > 0
        logger.info("[news] background refresh: %d new articles", inserted)
    except Exception as exc:
        logger.error("[news] background refresh error: %s", exc)


# ── /dashboard/summary ────────────────────────────────────────────────────────

@dashboard_router.get("/dashboard/summary", summary="Fast dashboard data aggregation")
def get_dashboard_summary():
    """
    Single endpoint returning everything the dashboard needs in ~2-3s:
    - companies[]        : S3 company roster with PDF/data file counts
    - sector_breakdown[] : companies grouped by sector with coverage %
    - kpi{}              : universe_count, docs_indexed, chunks_indexed, session_count
    - activity[]         : last 10 user_analytics sessions
    - recent_files[]     : last 10 PDFs from S3 (by LastModified)
    - recent_news[]      : last 12 news articles (for Guidance Intelligence + Signal panels)
    - vector_stats{}     : total_chunks in pgvector
    """
    result = {
        "companies":        [],
        "sector_breakdown": [],
        "kpi":              {},
        "activity":         [],
        "recent_files":     [],
        "recent_news":      [],
        "vector_stats":     {},
        "status":           "ok",
    }

    # ── 1. Company list + recent files from S3 ────────────────────────────────
    try:
        from modules.ingestion.company_loader import _get_s3_client, _BUCKET
        from modules.ingestion.companies import COMPANIES as COMPANY_MASTER

        sector_map = {c["id"]: c.get("sector", "—") for c in COMPANY_MASTER}
        name_map   = {c["id"]: c.get("id", c["id"]) for c in COMPANY_MASTER}

        client    = _get_s3_client()
        paginator = client.get_paginator("list_objects_v2")

        prefix_info: dict  = {}
        all_pdfs:    list  = []   # for recent_files

        for page in paginator.paginate(Bucket=_BUCKET):
            for obj in page.get("Contents", []):
                key      = obj.get("Key", "")
                size     = obj.get("Size", 0)
                modified = obj.get("LastModified")
                if not key:
                    continue

                prefix = key.split("/")[0] if "/" in key else key.rsplit(".", 1)[0]
                if prefix not in prefix_info:
                    prefix_info[prefix] = {"total": 0, "pdfs": 0, "data": 0}
                prefix_info[prefix]["total"] += 1
                low = key.lower()
                if low.endswith(".pdf"):
                    prefix_info[prefix]["pdfs"] += 1
                    all_pdfs.append({
                        "key":      key,
                        "company":  prefix,
                        "name":     key.split("/")[-1] if "/" in key else key,
                        "size_kb":  round(size / 1024, 1),
                        "modified": modified.isoformat() if modified else None,
                    })
                if low.endswith(".xlsx") or low.endswith(".json"):
                    prefix_info[prefix]["data"] += 1

        companies = []
        for ticker in sorted(prefix_info):
            info = prefix_info[ticker]
            if info["data"] == 0 and info["pdfs"] == 0:
                continue
            companies.append({
                "ticker":    ticker,
                "name":      name_map.get(ticker, ticker),
                "sector":    sector_map.get(ticker, "—"),
                "doc_count": info["pdfs"],
                "data_files":info["data"],
                "has_data":  info["data"] > 0,
            })

        result["companies"] = companies
        result["kpi"]["universe_count"] = len(companies)
        result["kpi"]["docs_indexed"]   = sum(c["doc_count"] for c in companies)

        # ── Sector breakdown ──────────────────────────────────────────────────
        sector_groups: dict = {}
        for c in companies:
            s = c["sector"]
            if s not in sector_groups:
                sector_groups[s] = {"sector": s, "count": 0, "docs": 0}
            sector_groups[s]["count"] += 1
            sector_groups[s]["docs"]  += c["doc_count"]

        total_cos = len(companies) or 1
        sector_list = sorted(sector_groups.values(), key=lambda x: -x["count"])
        max_count = max((s["count"] for s in sector_list), default=1)
        for s in sector_list:
            s["pct"] = round(s["count"] / max_count * 100)
        result["sector_breakdown"] = sector_list

        # ── Recent files (top 10 newest PDFs) ────────────────────────────────
        all_pdfs.sort(key=lambda x: x["modified"] or "", reverse=True)
        result["recent_files"] = all_pdfs[:10]

    except Exception as e:
        logger.warning("[dashboard/summary] S3 scan failed: %s", e)
        result["status"] = "partial"

    # ── 2. Recent activity from user_analytics ────────────────────────────────
    try:
        from core.database import execute_query
        rows = execute_query("""
            SELECT session_type, title, ticker, created_at
            FROM user_analytics
            ORDER BY created_at DESC
            LIMIT 10
        """)
        result["activity"] = [
            {
                "session_type": r["session_type"],
                "title":        r["title"],
                "ticker":       r["ticker"],
                "created_at":   r["created_at"].isoformat() if r.get("created_at") else None,
            }
            for r in rows
        ]
        result["kpi"]["session_count"] = len(rows)
    except Exception as e:
        logger.debug("[dashboard/summary] analytics query failed: %s", e)
        result["kpi"]["session_count"] = 0

    # ── 3. Vector store stats ─────────────────────────────────────────────────
    try:
        from modules.rag.vector_store import VectorStore
        vs = VectorStore()
        result["vector_stats"] = {"total_chunks": vs.total_chunks}
        result["kpi"]["chunks_indexed"] = vs.total_chunks
    except Exception as e:
        logger.debug("[dashboard/summary] vector store stats failed: %s", e)
        result["kpi"]["chunks_indexed"] = 0

    # ── 4. Recent news (for Guidance Intelligence + Alpha Signal panels) ──────
    try:
        from modules.news.db import get_dashboard_news
        articles = get_dashboard_news(limit=20)
        result["recent_news"] = [
            {
                "id":           a.get("id"),
                "symbol":       a.get("symbol", ""),
                "headline":     a.get("headline", ""),
                "summary":      a.get("summary", ""),
                "url":          a.get("url", ""),
                "published_at": a.get("published_at").isoformat() if a.get("published_at") else None,
                "source":       a.get("source", ""),
                "sentiment":    a.get("sentiment_score", 0),
            }
            for a in (articles or [])
        ]
    except Exception as e:
        logger.debug("[dashboard/summary] news query failed: %s", e)

    return result


# ── /dashboard/history ────────────────────────────────────────────────────────

@dashboard_router.get("/dashboard/history", summary="Monthly trend for Score Evolution chart")
def get_dashboard_history(months: int = 7):
    """
    Monthly engagement trend for the Score Evolution chart.
    Uses log-scale normalization to prevent hockey-stick distortion when
    all activity is concentrated in a single month.
    Returns has_data=false if data is too sparse to be meaningful.
    """
    import math
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    buckets = []
    for i in range(months - 1, -1, -1):
        d = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        buckets.append({"year": d.year, "month": d.month, "label": d.strftime("%b")})

    session_by_month: dict = {}
    news_by_month:    dict = {}

    try:
        from core.database import execute_query
        rows = execute_query("""
            SELECT EXTRACT(YEAR FROM created_at)::int  AS yr,
                   EXTRACT(MONTH FROM created_at)::int AS mo,
                   COUNT(*) AS cnt
            FROM user_analytics
            WHERE created_at >= NOW() - INTERVAL '8 months'
            GROUP BY yr, mo
        """)
        for r in rows:
            session_by_month[(r["yr"], r["mo"])] = int(r["cnt"])
    except Exception as e:
        logger.debug("[dashboard/history] sessions query failed: %s", e)

    try:
        from core.database import execute_query
        rows = execute_query("""
            SELECT EXTRACT(YEAR FROM published_at)::int  AS yr,
                   EXTRACT(MONTH FROM published_at)::int AS mo,
                   COUNT(*) AS cnt
            FROM company_news
            WHERE published_at >= NOW() - INTERVAL '8 months'
            GROUP BY yr, mo
        """)
        for r in rows:
            news_by_month[(r["yr"], r["mo"])] = int(r["cnt"])
    except Exception as e:
        logger.debug("[dashboard/history] news query failed: %s", e)

    # ── Detect top-heavy data: if >80% of all sessions are in 1 month, skip ──
    total_s = sum(session_by_month.values()) or 0
    total_n = sum(news_by_month.values()) or 0
    months_with_data = sum(
        1 for b in buckets
        if session_by_month.get((b["year"], b["month"]), 0) > 0
        or news_by_month.get((b["year"], b["month"]), 0) > 0
    )

    # Require at least 2 months with data AND no single month holding >70% of sessions
    max_month_s = max(session_by_month.values(), default=0)
    is_top_heavy = total_s > 0 and max_month_s / total_s > 0.70
    is_too_sparse = months_with_data < 2

    if is_top_heavy or is_too_sparse:
        return {"trend": [], "has_data": False, "months": months,
                "reason": "top_heavy" if is_top_heavy else "sparse"}

    # ── Log-scale raw scores ──────────────────────────────────────────────────
    raw_scores = []
    for b in buckets:
        key = (b["year"], b["month"])
        s   = session_by_month.get(key, 0)
        n   = news_by_month.get(key, 0)
        # log1p prevents dominance of outlier months
        raw = math.log1p(s) * 2.0 + math.log1p(n) * 1.0
        raw_scores.append(raw)

    # ── Rescale raw values to [58, 88] range ─────────────────────────────────
    rmin, rmax = min(raw_scores), max(raw_scores)
    spread = rmax - rmin if rmax > rmin else 1.0

    trend = []
    for i, b in enumerate(buckets):
        key      = (b["year"], b["month"])
        normalized = (raw_scores[i] - rmin) / spread   # 0.0 → 1.0
        score    = round(58 + normalized * 30)           # 58 → 88
        score    = max(58, min(88, score))
        trend.append({
            "m":        b["label"],
            "v":        score,
            "sessions": session_by_month.get(key, 0),
            "articles": news_by_month.get(key, 0),
        })

    has_data = any(t["sessions"] > 0 or t["articles"] > 0 for t in trend)
    return {"trend": trend if has_data else [], "has_data": has_data, "months": months}
