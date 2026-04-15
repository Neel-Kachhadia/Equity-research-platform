"""
EREBUS · PDF Scraper (Investor Relations pages)
================================================
Scrapes financial PDFs from company IR pages.

Features:
  - Keyword allow/reject filtering so only relevant docs are downloaded
  - Timestamped filenames → no overwrites, natural version history
  - Minimum size validation (rejects HTML error pages served as PDFs)
  - Random User-Agent rotation to avoid trivial bot detection
  - 1-second inter-request rate control
  - 3-attempt retry with exponential backoff per URL
  - Multi-URL support: tries next URL if first yields 0 PDFs
"""

import hashlib
import logging
import random
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# -- Keyword filters -----------------------------------------------------------
VALID_KEYWORDS: list[str] = [
    "results",
    "earnings",
    "financial",
    "statement",
    "quarter",
    "annual",
    "report",
    "q1", "q2", "q3", "q4",
    "fy", "fiscal",
    "balance",
    "profit",
    "loss",
    # Additional high-value document types
    "transcript",      # investor / earnings call transcripts
    "presentation",    # investor presentations / decks
    "investor",        # investor packs
    "notice",          # board meeting / AGM notices
    "agm",             # Annual General Meeting
    "egm",             # Extraordinary General Meeting
    "dividend",        # dividend announcements
    "press-release",   # quarterly press releases
    "standalone",      # standalone financial statements
    "consolidated",    # consolidated financial statements
    "auditor",         # auditor reports
    "disclosure",      # SEBI / stock exchange disclosures
]

IGNORE_KEYWORDS: list[str] = [
    "policy",
    "csr",
    # "press" removed — press releases contain quarterly financial data
    "sustainability",
    "esg",
    "code-of-conduct",
    "whistle",
    "vigil",
    "nomination",
    "brochure",        # marketing brochures
    "catalogue",
    "product",
    "training",
]

# Non-English filename / anchor patterns — skip immediately (regional language docs)
# Covers: Marathi, Hindi, Gujarati, Tamil, Telugu, Kannada, Bengali, Malayalam,
#         Punjabi, Odia, Urdu, and common regional ad/newspaper terms.
NON_ENGLISH_PATTERNS: list[str] = [
    "marathi", "hindi", "gujarati", "tamil", "telugu", "kannada",
    "bengali", "malayalam", "punjabi", "odia", "urdu", "hindi",
    "-advt",       # e.g. marathi-advt.pdf
    "_advt",
    "newspaper",   # regional statutory newspaper advertisements
    "samachar",    # Hindi: news
    "vartapatra",  # Marathi: newspaper
    "patrika",     # Hindi/Gujarati: newspaper
    "-notice-hindi",
    "-notice-marathi",
]

# -- Config --------------------------------------------------------------------
MIN_PDF_BYTES   = 10_000     # anything smaller is probably an error page
MAX_PDF_BYTES   = 80_000_000 # 80 MB upper sanity limit (some annual reports are large)
RETRY_ATTEMPTS  = 3
RETRY_DELAY_S   = 2
REQUEST_TIMEOUT = 30         # seconds (increased for large PDFs)
INTER_REQ_SLEEP = 1.0        # seconds between requests (be polite)
MAX_PDFS_PER_CO = 30         # increased to get full doc coverage per company

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


# -- Public API ----------------------------------------------------------------

def scrape_pdfs(
    company_id: str,
    ir_urls: list[str],
    max_pdfs: int = MAX_PDFS_PER_CO,
) -> list[dict]:
    """
    Scrape financial PDFs from one or more IR pages.

    Tries each URL in `ir_urls` in order; stops when it finds PDFs.

    Returns:
        list of {
            "company_id" : str,
            "filename"   : str,          # timestamped, e.g. "2024-04_annual_report.pdf"
            "content"    : bytes,
            "source_url" : str,
        }
        May return [] if nothing valid was found.
    """
    results: list[dict] = []

    for ir_url in ir_urls:
        # ── Direct PDF URL: download immediately without link-scraping ──────
        if ir_url.lower().endswith(".pdf"):
            logger.info("[pdf] %s — direct PDF URL: %s", company_id, ir_url)
            content = _download_pdf(ir_url)
            if content is not None:
                filename = _make_filename(ir_url, "")
                results.append({
                    "company_id": company_id,
                    "filename":   filename,
                    "content":    content,
                    "source_url": ir_url,
                })
                logger.info(
                    "[pdf] [OK] %s — downloaded %s (%d KB)",
                    company_id, filename, len(content) // 1024,
                )
            continue  # move to next URL (don't try to scrape this as an HTML page)

        # ── IR page: extract PDF links then download each ───────────────────
        logger.info("[pdf] %s — trying IR page: %s", company_id, ir_url)
        links = _extract_pdf_links(ir_url)

        if not links:
            logger.warning("[pdf] No relevant PDF links found at %s", ir_url)
            continue

        logger.info("[pdf] %s — found %d candidate links", company_id, len(links))

        for href, anchor_text in links[:max_pdfs]:
            time.sleep(INTER_REQ_SLEEP)
            content = _download_pdf(href)
            if content is None:
                continue

            filename = _make_filename(href, anchor_text)
            results.append({
                "company_id": company_id,
                "filename":   filename,
                "content":    content,
                "source_url": href,
            })
            logger.info(
                "[pdf] [OK] %s — downloaded %s (%d KB)",
                company_id, filename, len(content) // 1024,
            )

        if results:
            break   # HTML page had PDFs — no need to try remaining fallback URLs

    if not results:
        logger.warning("[pdf] [WARN]  %s — no PDFs downloaded from any IR URL", company_id)

    return results


# -- Internal helpers ----------------------------------------------------------

def _headers() -> dict:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept":     "text/html,application/pdf,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _extract_pdf_links(page_url: str) -> list[tuple[str, str]]:
    """
    Fetch `page_url`, parse all <a href="...pdf"> links,
    and filter by VALID_KEYWORDS / IGNORE_KEYWORDS.

    Returns list of (absolute_url, anchor_text).
    """
    try:
        resp = _get_with_retry(page_url)
        if resp is None:
            return []
    except Exception as e:
        logger.error("[pdf] Failed to fetch IR page %s: %s", page_url, e)
        return []

    soup  = BeautifulSoup(resp.text, "html.parser")
    base  = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
    found = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        text = tag.get_text(" ", strip=True).lower()
        href_lower = href.lower()

        # Must look like a PDF (link or content-type)
        if not href_lower.endswith(".pdf") and "pdf" not in href_lower:
            continue

        # Absolute URL
        if not href.startswith("http"):
            href = urljoin(base, href)

        # Language filter: skip non-English documents (regional language ads,
        # statutory notices in Marathi/Hindi, etc.)
        combined_lower = href_lower + " " + text
        if any(pat in combined_lower for pat in NON_ENGLISH_PATTERNS):
            logger.info("[pdf] skip (non-English): %s", href)
            continue

        # Must match at least one VALID keyword
        if not any(kw in combined_lower for kw in VALID_KEYWORDS):
            logger.debug("[pdf] skip (no valid keyword): %s", href)
            continue

        # Must NOT match any IGNORE keyword
        if any(kw in combined_lower for kw in IGNORE_KEYWORDS):
            logger.debug("[pdf] skip (ignored keyword): %s", href)
            continue

        found.append((href, text))

    # De-duplicate preserving order
    seen: set[str] = set()
    deduped = []
    for href, text in found:
        if href not in seen:
            seen.add(href)
            deduped.append((href, text))

    return deduped


def _download_pdf(url: str) -> Optional[bytes]:
    """Download a single PDF URL with retry. Returns bytes or None."""
    resp = _get_with_retry(url, stream=True)
    if resp is None:
        return None

    content = resp.content

    # Size validation
    if len(content) < MIN_PDF_BYTES:
        logger.warning(
            "[pdf] [WARN]  Skipping %s — too small (%d bytes, min=%d)",
            url, len(content), MIN_PDF_BYTES,
        )
        return None

    if len(content) > MAX_PDF_BYTES:
        logger.warning(
            "[pdf] [WARN]  Skipping %s — too large (%d MB)",
            url, len(content) // 1_000_000,
        )
        return None

    # Confirm it's actually a PDF (magic bytes)
    if not content.startswith(b"%PDF"):
        logger.warning("[pdf] [WARN]  Skipping %s — not a valid PDF (no %%PDF header)", url)
        return None

    return content


def _get_with_retry(url: str, stream: bool = False) -> Optional[requests.Response]:
    """GET a URL with retry+backoff. Returns Response or None on final failure."""
    delay = RETRY_DELAY_S
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.get(
                url,
                headers=_headers(),
                timeout=REQUEST_TIMEOUT,
                stream=stream,
                allow_redirects=True,
            )
            resp.raise_for_status()
            return resp

        except requests.RequestException as e:
            logger.warning(
                "[pdf] Attempt %d/%d failed for %s: %s",
                attempt, RETRY_ATTEMPTS, url, e,
            )
            if attempt < RETRY_ATTEMPTS:
                time.sleep(delay)
                delay *= 2

    logger.error("[pdf] [FAIL] All retries exhausted for: %s", url)
    return None


def _make_filename(url: str, anchor_text: str) -> str:
    """
    Build a timestamped, slug-safe filename.
    e.g. "2024-04_tcs-q4-results.pdf"
    """
    # Use URL basename if it's informative, else fall back to anchor text
    url_name = url.rstrip("/").split("/")[-1]
    if len(url_name) > 6 and url_name.lower().endswith(".pdf"):
        base = url_name[:-4]
    elif anchor_text:
        base = anchor_text[:60]
    else:
        # Last-resort: short hash of URL for uniqueness
        base = hashlib.md5(url.encode()).hexdigest()[:8]

    # Slug-ify: lowercase, replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w]+", "-", base.lower()).strip("-")
    ts   = datetime.utcnow().strftime("%Y-%m-%d")
    return f"{ts}_{slug}.pdf"
