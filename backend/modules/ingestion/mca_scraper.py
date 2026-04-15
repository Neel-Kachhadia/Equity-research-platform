"""
EREBUS · MCA + BSE Filing Scraper
====================================
Downloads financial filings from two official Indian regulatory sources:

  1. BSE Filing API  — primary route (public JSON, no session needed)
                       Fetches annual reports + quarterly results PDFs
  2. MCA eFiling     — secondary route (Ministry of Corporate Affairs)
                       Fetches AOC-4 (financial statements) and MGT-7 (annual returns)

Why two sources?
  - BSE is easier to access programmatically (JSON API)
  - MCA is the ground-truth legal filing; BSE may mirror it with a delay
  - Running both maximises recall

Features:
  - Keyword allow/reject filtering (same ruleset as pdf_scraper.py)
  - Min size validation (rejects HTML error pages)
  - Retry + backoff for network failures
  - 1s inter-request rate control
  - Results returned in same format as pdf_scraper.py
    → { company_id, filename, content, source_url, source }
"""

import hashlib
import json
import logging
import random
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

# -- Keyword filters (shared with pdf_scraper) ---------------------------------
VALID_KEYWORDS = [
    "annual", "report", "results", "financial", "statement",
    "quarter", "earnings", "revenue", "profit", "loss",
    "balance", "q1", "q2", "q3", "q4", "fy", "aoc-4",
]
IGNORE_KEYWORDS = [
    "policy", "csr", "press", "sustainability", "esg",
    "governance", "whistle", "vigil", "nomination", "code-of-conduct",
]

# -- Config --------------------------------------------------------------------
MIN_PDF_BYTES   = 10_000
MAX_PDF_BYTES   = 80_000_000   # 80 MB (MCA filings can be large)
RETRY_ATTEMPTS  = 3
RETRY_DELAY_S   = 2
REQUEST_TIMEOUT = 25
INTER_REQ_SLEEP = 1.0
MAX_DOCS        = 8             # per company per source

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

# -- BSE endpoints -------------------------------------------------------------
# Both Strscripcd AND scripcode params are required — the API returns HTML
# when either is missing (tested April 2026)
_BSE_ANNUAL_REPORT_URL = (
    "https://api.bseindia.com/BseIndiaAPI/api/AnnualReport/w"
    "?Strscripcd={bse_code}&scripcode={bse_code}"
)
_BSE_QUARTERLY_URL = (
    "https://api.bseindia.com/BseIndiaAPI/api/AnnualReport/w"
    "?Strscripcd={bse_code}&scripcode={bse_code}&type=QR"
)
_BSE_PDF_BASE = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/"

# -- MCA eFiling endpoints -----------------------------------------------------
_MCA_SEARCH_URL = (
    "https://efiling.mca.gov.in/eFiling/helpdeskSearch.do"
)
_MCA_DOC_BASE   = "https://efiling.mca.gov.in/eFiling/"


# -- Public API ----------------------------------------------------------------

def scrape_mca_bse(
    company_id: str,
    cin: Optional[str] = None,
    bse_code: Optional[str] = None,
    max_docs: int = MAX_DOCS,
) -> list[dict]:
    """
    Download financial filings for a company from BSE and/or MCA.

    Args:
        company_id: internal EREBUS id (used for filenames and S3 keys)
        cin:        MCA Corporate Identification Number, e.g. 'L22210MH1995PLC084781'
        bse_code:   BSE scrip code, e.g. '532540' for TCS
        max_docs:   maximum PDFs to return

    Returns:
        list of {
            "company_id" : str,
            "filename"   : str,   # timestamped
            "content"    : bytes,
            "source_url" : str,
            "source"     : "bse" | "mca",
        }
    """
    results: list[dict] = []

    # -- 1. BSE route ---------------------------------------------------------
    if bse_code:
        logger.info("[mca_bse] %s — Fetching BSE filings (scrip %s)", company_id, bse_code)
        bse_items = _fetch_bse_annual(company_id, bse_code)
        bse_items += _fetch_bse_quarterly(company_id, bse_code)
        results.extend(bse_items[:max_docs])
        logger.info("[mca_bse] %s — BSE: %d docs", company_id, len(bse_items))
    else:
        logger.warning("[mca_bse] %s — No BSE code configured, skipping BSE route", company_id)

    # -- 2. MCA route ---------------------------------------------------------
    if cin and len(results) < max_docs:
        logger.info("[mca_bse] %s — Fetching MCA filings (CIN %s)", company_id, cin)
        mca_items = _fetch_mca_filings(company_id, cin)
        remaining  = max_docs - len(results)
        results.extend(mca_items[:remaining])
        logger.info("[mca_bse] %s — MCA: %d docs", company_id, len(mca_items))
    elif not cin:
        logger.warning("[mca_bse] %s — No CIN configured, skipping MCA route", company_id)

    if not results:
        logger.warning("[mca_bse] %s — No filings retrieved from BSE or MCA", company_id)

    return results


# -- BSE helpers ---------------------------------------------------------------

def _fetch_bse_annual(company_id: str, bse_code: str) -> list[dict]:
    """Fetch annual reports from BSE filing API."""
    url = _BSE_ANNUAL_REPORT_URL.format(bse_code=bse_code)
    return _process_bse_response(company_id, url, tag="annual")


def _fetch_bse_quarterly(company_id: str, bse_code: str) -> list[dict]:
    """Fetch quarterly results PDFs from BSE filing API."""
    url = _BSE_QUARTERLY_URL.format(bse_code=bse_code)
    return _process_bse_response(company_id, url, tag="quarterly")


def _process_bse_response(company_id: str, api_url: str, tag: str) -> list[dict]:
    """Call BSE JSON API, extract PDF links, download and validate."""
    resp = _get_with_retry(api_url, accept="application/json")
    if resp is None:
        return []

    try:
        data = resp.json()
    except Exception as e:
        logger.warning("[mca_bse] BSE JSON parse failed (%s): %s", api_url, e)
        return []

    # BSE returns {"Table": [...]} or a list directly
    rows = data if isinstance(data, list) else data.get("Table", data.get("Table1", []))
    if not rows:
        logger.warning("[mca_bse] BSE empty response for %s (%s)", company_id, tag)
        return []

    results = []
    for row in rows:
        # Different BSE endpoints use different field names
        pdf_name = (
            row.get("PDFFLAG") or row.get("ATTACHMENTNAME") or
            row.get("PDF_NAME") or row.get("FileName") or ""
        )
        title = (
            row.get("SUBJECT") or row.get("NEWSSUB") or
            row.get("SLONGNAME") or row.get("SCRIPNAME") or
            row.get("ReportName") or ""
        )

        if not pdf_name:
            continue

        combined = (pdf_name + " " + title).lower()
        if not any(kw in combined for kw in VALID_KEYWORDS):
            continue
        if any(kw in combined for kw in IGNORE_KEYWORDS):
            continue

        pdf_url = (
            pdf_name if pdf_name.startswith("http")
            else f"{_BSE_PDF_BASE}{pdf_name}"
        )

        time.sleep(INTER_REQ_SLEEP)
        content = _download_pdf_bytes(pdf_url)
        if content is None:
            continue

        filename = _make_filename(pdf_name, title or tag)
        results.append({
            "company_id": company_id,
            "filename":   filename,
            "content":    content,
            "source_url": pdf_url,
            "source":     "bse",
        })
        logger.info("[mca_bse] BSE [OK] %s — %s (%d KB)", company_id, filename, len(content) // 1024)

    return results


# -- MCA helpers ---------------------------------------------------------------

def _fetch_mca_filings(company_id: str, cin: str) -> list[dict]:
    """
    Download publicly available AOC-4 (financial statements) and MGT-7 (annual return)
    from MCA eFiling portal using the company's CIN.

    MCA public filing search URL pattern:
        https://efiling.mca.gov.in/eFiling/helpdeskSearch.do

    For publicly listed companies, AOC-4 and MGT-7 forms are public.
    """
    # MCA public document index via the XBRL viewer API (no auth required)
    # This endpoint is used by the MCA public portal's "company search"
    mca_search = (
        f"https://efiling.mca.gov.in/eFiling/helpdeskSearch.do"
        f"?cin={cin}&filingTypes=AOC-4,MGT-7&companyCategory=public"
    )

    # Attempt 1: public search API
    resp = _get_with_retry(mca_search)
    if resp is not None and resp.status_code == 200:
        results = _parse_mca_search(company_id, cin, resp)
        if results:
            return results

    # Attempt 2: BSE XBRL mirror of MCA filings (more accessible)
    # BSE hosts XBRL-tagged MCA filings at:
    xbrl_url = (
        f"https://www.bseindia.com/corporates/xbrlSearch.html"
        f"?companyName={company_id}&type=Annual"
    )
    logger.info("[mca_bse] MCA direct access limited for %s — trying BSE XBRL mirror", company_id)
    resp2 = _get_with_retry(xbrl_url)
    if resp2 is not None:
        return _parse_mca_search(company_id, cin, resp2)

    logger.warning("[mca_bse] MCA: Could not retrieve filings for CIN=%s", cin)
    return []


def _parse_mca_search(company_id: str, cin: str, resp: requests.Response) -> list[dict]:
    """
    Parse MCA search response. Extracts PDF links from HTML or JSON.
    MCA portal serves HTML pages with embedded filing links.
    """
    results = []
    text = resp.text

    # Try JSON first (some MCA API endpoints return JSON)
    try:
        data = resp.json()
        filings = data.get("filings", data.get("documents", []))
        for f in filings:
            url = f.get("url") or f.get("documentUrl")
            title = f.get("formType", "") + " " + f.get("description", "")
            if not url:
                continue
            combined = (url + " " + title).lower()
            if not any(kw in combined for kw in ["aoc", "mgt", "annual", "financial"]):
                continue
            time.sleep(INTER_REQ_SLEEP)
            content = _download_pdf_bytes(url)
            if content:
                results.append({
                    "company_id": company_id,
                    "filename":   _make_filename(url, title),
                    "content":    content,
                    "source_url": url,
                    "source":     "mca",
                })
        return results
    except Exception:
        pass

    # HTML fallback — extract PDF links
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    base = "https://efiling.mca.gov.in"

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        anchor = tag.get_text(" ", strip=True).lower()
        if not (href.lower().endswith(".pdf") or "pdf" in href.lower()):
            continue
        combined = href.lower() + " " + anchor
        if not any(kw in combined for kw in VALID_KEYWORDS):
            continue
        if any(kw in combined for kw in IGNORE_KEYWORDS):
            continue
        full_url = href if href.startswith("http") else urljoin(base, href)
        time.sleep(INTER_REQ_SLEEP)
        content = _download_pdf_bytes(full_url)
        if content:
            results.append({
                "company_id": company_id,
                "filename":   _make_filename(full_url, anchor),
                "content":    content,
                "source_url": full_url,
                "source":     "mca",
            })
            logger.info("[mca_bse] MCA [OK] %s — %s (%d KB)",
                        company_id, results[-1]["filename"], len(content) // 1024)

    return results


# -- Shared utilities ----------------------------------------------------------

def _download_pdf_bytes(url: str) -> Optional[bytes]:
    """Download a PDF URL and validate it. Returns bytes or None."""
    resp = _get_with_retry(url, stream=True)
    if resp is None:
        return None
    content = resp.content
    if len(content) < MIN_PDF_BYTES:
        logger.warning("[mca_bse] Too small (%d bytes), skipping: %s", len(content), url[:80])
        return None
    if len(content) > MAX_PDF_BYTES:
        logger.warning("[mca_bse] Too large (%d MB), skipping: %s",
                       len(content) // 1_000_000, url[:80])
        return None
    if not content.startswith(b"%PDF"):
        logger.warning("[mca_bse] Not a PDF (no %%PDF header): %s", url[:80])
        return None
    return content


def _get_with_retry(
    url: str,
    stream: bool = False,
    accept: str = "text/html,application/pdf,*/*",
) -> Optional[requests.Response]:
    """GET with retry and exponential backoff."""
    delay = RETRY_DELAY_S
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.bseindia.com/",
    }
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.get(
                url, headers=headers, timeout=REQUEST_TIMEOUT,
                stream=stream, allow_redirects=True,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning("[mca_bse] Attempt %d/%d failed [%s]: %s",
                           attempt, RETRY_ATTEMPTS, url[:60], e)
            if attempt < RETRY_ATTEMPTS:
                time.sleep(delay)
                delay *= 2

    logger.error("[mca_bse] All retries failed: %s", url[:80])
    return None


def _make_filename(url: str, title: str) -> str:
    """Build a safe, timestamped filename."""
    base = url.rstrip("/").split("/")[-1]
    if not base or not base.lower().endswith(".pdf"):
        base = re.sub(r"[^\w]+", "-", (title or "mca-filing")[:60].lower()).strip("-")
    else:
        base = base[:-4]

    slug = re.sub(r"[^\w]+", "-", base.lower()).strip("-")
    ts   = datetime.utcnow().strftime("%Y-%m-%d")
    return f"{ts}_{slug}.pdf"
