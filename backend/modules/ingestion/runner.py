"""
EREBUS · Ingestion Pipeline Runner
===================================
Orchestrates the complete ingestion workflow for all companies.

Sources per company:
  1. Yahoo Finance  — price history + income / balance / cashflow (JSON → S3)
  2. IR page PDFs   — investor-relations page scraping (pdf_scraper)
  3. MCA + BSE      — regulatory filings (AOC-4, annual reports via BSE API)

Usage:
  from modules.ingestion.runner import run_ingestion_pipeline, IngestionResult
  result = run_ingestion_pipeline(
      company_ids=["TCS", "INFY"],
      fetch_prices=True,
      fetch_pdfs=True,
      fetch_mca=True,
      dry_run=False,
  )
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .companies import ALL_COMPANY_IDS, get_ticker, get_ir_urls, get_cin, get_bse_code
from .yahoo_scraper import fetch_yahoo_data, YahooDataError
from .pdf_scraper import scrape_pdfs
from .mca_scraper import scrape_mca_bse
from .s3_uploader import upload_to_s3, object_exists, _get_s3_client

logger = logging.getLogger(__name__)


# -- Result dataclass ----------------------------------------------------------

@dataclass
class IngestionResult:
    """Result of a single pipeline run."""
    run_id:          str
    started_at:      datetime
    completed_at:    Optional[datetime]  = None
    total_companies: int                 = 0
    successful:      int                 = 0
    failed:          int                 = 0
    errors:          List[Dict]          = field(default_factory=list)
    details:         Dict[str, Any]      = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def summary(self) -> str:
        return (
            f"Run {self.run_id}: "
            f"{self.successful}/{self.total_companies} OK, "
            f"{self.failed} failed, "
            f"{len(self.errors)} errors, "
            f"{self.duration_seconds:.1f}s"
            if self.duration_seconds else ""
        )


# -- Main orchestrator ---------------------------------------------------------

def run_ingestion_pipeline(
    company_ids: Optional[List[str]] = None,
    fetch_prices: bool = True,
    fetch_pdfs:   bool = False,
    fetch_mca:    bool = False,
    dry_run:      bool = False,
) -> IngestionResult:
    """
    Run full ingestion pipeline for specified companies.

    Args:
        company_ids:  List of EREBUS company ids (default: all 25)
        fetch_prices: Fetch Yahoo Finance price history + financials
        fetch_pdfs:   Scrape investor-relations page PDFs
        fetch_mca:    Scrape regulatory filings from BSE API + MCA eFiling
        dry_run:      If True, skip S3 uploads (useful for testing)

    Returns:
        IngestionResult dataclass with full per-company details
    """
    company_ids = company_ids or ALL_COMPANY_IDS
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]

    result = IngestionResult(
        run_id=run_id,
        started_at=datetime.utcnow(),
        total_companies=len(company_ids),
    )

    logger.info("[Pipeline] -- Run %s ---------------------------------", run_id)
        # Eagerly init S3 client before the loop so all companies share it
    try:
        _get_s3_client()
    except Exception as _e:
        logger.warning("[Pipeline] S3 client init failed: %s", _e)

    logger.info("[Pipeline] Companies : %d", len(company_ids))
    logger.info("[Pipeline] Sources   : prices=%s  ir_pdfs=%s  mca/bse=%s",
                fetch_prices, fetch_pdfs, fetch_mca)
    logger.info("[Pipeline] Dry run   : %s", dry_run)

    for idx, company_id in enumerate(company_ids, 1):
        logger.info("[Pipeline] [%d/%d] %s", idx, len(company_ids), company_id)
        company_result: Dict[str, Any] = {
            "company_id": company_id,
            "prices":     None,
            "ir_pdfs":    None,
            "mca_pdfs":   None,
        }

        try:
            # -- 1. Yahoo Finance ---------------------------------------------
            if fetch_prices:
                company_result["prices"] = _run_yahoo(
                    company_id, dry_run, result.errors
                )

            # -- 2. IR page PDFs ----------------------------------------------
            if fetch_pdfs:
                ir_urls = get_ir_urls(company_id)
                if ir_urls:
                    company_result["ir_pdfs"] = _run_ir_pdfs(
                        company_id, ir_urls, dry_run, result.errors
                    )
                else:
                    logger.warning("[Pipeline] No IR URLs for %s", company_id)

            # -- 3. MCA + BSE regulatory filings -----------------------------
            if fetch_mca:
                cin      = get_cin(company_id)
                bse_code = get_bse_code(company_id)
                company_result["mca_pdfs"] = _run_mca_bse(
                    company_id, cin, bse_code, dry_run, result.errors
                )

            result.successful += 1
            result.details[company_id] = company_result
            logger.info("[Pipeline] %s — done", company_id)

        except Exception as e:
            result.failed += 1
            result.errors.append({
                "company_id": company_id, "source": "pipeline", "error": str(e)
            })
            logger.error("[Pipeline] %s — unexpected failure: %s", company_id, e)

    result.completed_at = datetime.utcnow()
    _log_summary(result)
    return result


# -- Per-source runners --------------------------------------------------------

def _run_yahoo(
    company_id: str,
    dry_run: bool,
    errors: List[Dict],
) -> Optional[Dict]:
    """Fetch Yahoo Finance data and upload as JSON to S3."""
    try:
        ticker = get_ticker(company_id)
        data   = fetch_yahoo_data(ticker, period="5y")

        if not dry_run:
            key = f"{company_id}/yahoo_data_{datetime.utcnow().strftime('%Y%m%d')}.json"
            upload_to_s3(
                key=key,
                content=json.dumps(data, default=str).encode(),
                content_type="application/json",
                metadata={"company_id": company_id, "source": "yahoo"},
            )

        logger.info("[Pipeline] Yahoo %s — %d price points", company_id, len(data["prices"]))
        return {"count": len(data["prices"]), "financials": data.get("financials") is not None}

    except YahooDataError as e:
        errors.append({"company_id": company_id, "source": "yahoo", "error": str(e)})
        logger.error("[Pipeline] Yahoo failed for %s: %s", company_id, e)
        return None


def _run_ir_pdfs(
    company_id: str,
    ir_urls: List[str],
    dry_run: bool,
    errors: List[Dict],
) -> Dict:
    """Scrape IR page PDFs and upload to S3."""
    try:
        pdfs = scrape_pdfs(company_id, ir_urls, max_pdfs=8)
        uploaded = []

        for pdf in pdfs:
            s3_key = _pdf_s3_key(company_id, pdf["filename"], source="ir")
            if not dry_run:
                if object_exists(s3_key):
                    logger.info("[Pipeline] IR PDF already in S3, skip: %s", s3_key)
                    continue
                upload_to_s3(
                    key=s3_key,
                    content=pdf["content"],
                    content_type="application/pdf",
                    metadata={"company_id": company_id, "source_url": pdf["source_url"]},
                )
            uploaded.append(s3_key)

        logger.info("[Pipeline] IR PDFs %s — %d uploaded", company_id, len(uploaded))
        return {"downloaded": len(pdfs), "uploaded": len(uploaded)}

    except Exception as e:
        errors.append({"company_id": company_id, "source": "ir_pdf", "error": str(e)})
        logger.error("[Pipeline] IR PDF failed for %s: %s", company_id, e)
        return {"downloaded": 0, "uploaded": 0}


def _run_mca_bse(
    company_id: str,
    cin: Optional[str],
    bse_code: Optional[str],
    dry_run: bool,
    errors: List[Dict],
) -> Dict:
    """Scrape MCA/BSE regulatory filings and upload to S3."""
    try:
        docs = scrape_mca_bse(company_id, cin=cin, bse_code=bse_code, max_docs=6)
        uploaded = []

        for doc in docs:
            source   = doc.get("source", "mca")   # "bse" or "mca"
            s3_key   = _pdf_s3_key(company_id, doc["filename"], source=source)
            if not dry_run:
                if object_exists(s3_key):
                    logger.info("[Pipeline] MCA/BSE PDF already in S3, skip: %s", s3_key)
                    continue
                upload_to_s3(
                    key=s3_key,
                    content=doc["content"],
                    content_type="application/pdf",
                    metadata={
                        "company_id": company_id,
                        "source": source,
                        "source_url": doc["source_url"],
                    },
                )
            uploaded.append(s3_key)

        logger.info("[Pipeline] MCA/BSE %s — %d uploaded", company_id, len(uploaded))
        return {"downloaded": len(docs), "uploaded": len(uploaded)}

    except Exception as e:
        errors.append({"company_id": company_id, "source": "mca_bse", "error": str(e)})
        logger.error("[Pipeline] MCA/BSE failed for %s: %s", company_id, e)
        return {"downloaded": 0, "uploaded": 0}


# -- S3 key builder ------------------------------------------------------------

def _pdf_s3_key(company_id: str, filename: str, source: str = "ir") -> str:
    """
    Build an S3 key for a PDF filing.

    Layout:
        {company_id}/
            Annual_Reports/    ← annual/report/fy keywords → Annual_Reports
            Quarterly_Results/ ← q1/q2/q3/q4/quarter/results keywords
            MCA_Filings/       ← source == 'mca'
            BSE_Filings/       ← source == 'bse'
    """
    lower = filename.lower()
    if source == "mca":
        folder = "MCA_Filings"
    elif source == "bse":
        # BSE documents: quarterly vs annual
        if any(kw in lower for kw in ["q1", "q2", "q3", "q4", "quarter", "result"]):
            folder = "Quarterly_Results"
        else:
            folder = "Annual_Reports"
    else:
        # IR page PDFs
        if any(kw in lower for kw in ["q1", "q2", "q3", "q4", "quarter"]):
            folder = "Quarterly_Results"
        else:
            folder = "Annual_Reports"

    return f"{company_id}/{folder}/{filename}"


# -- Summary logger ------------------------------------------------------------

def _log_summary(result: IngestionResult) -> None:
    logger.info("[Pipeline] -- Summary --------------------------------------")
    logger.info("[Pipeline] Run    : %s", result.run_id)
    logger.info("[Pipeline] Total  : %d companies", result.total_companies)
    logger.info("[Pipeline] OK     : %d", result.successful)
    logger.info("[Pipeline] Failed : %d", result.failed)
    logger.info("[Pipeline] Errors : %d", len(result.errors))
    if result.errors:
        for e in result.errors[:5]:   # show first 5
            logger.info("[Pipeline]   -> [%s/%s] %s",
                        e["company_id"], e["source"], e["error"][:100])
    logger.info("[Pipeline] Time   : %.1fs", result.duration_seconds or 0)
    logger.info("[Pipeline] ------------------------------------------------")