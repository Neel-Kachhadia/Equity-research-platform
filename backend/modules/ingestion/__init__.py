"""
EREBUS · Ingestion Module
=========================
Multi-source data ingestion for financial analysis.

Sources:
    - Yahoo Finance  — price history + income / balance / cashflow
    - IR page PDFs   — investor-relations page scraping
    - BSE API        — annual reports + quarterly results (primary regulatory source)
    - MCA eFiling    — AOC-4 / MGT-7 filings (secondary regulatory source)
    - Screener.in Excel — pre-formatted financials already in S3

Public API:
    from modules.ingestion import (
        # S3 / Excel Screener.in loader
        load_company, CompanyDataError,

        # Scrapers
        scrape_pdfs,                # IR page PDFs
        scrape_mca_bse,             # BSE API + MCA eFiling regulatory docs
        fetch_yahoo_data,           # single-ticker Yahoo fetch
        fetch_multiple_companies,   # batch Yahoo fetch
        YahooDataError,

        # Pipeline
        run_ingestion_pipeline, IngestionResult,

        # S3
        upload_to_s3, S3UploadError, object_exists,

        # Company master config
        COMPANIES, COMPANY_MAP, ALL_COMPANY_IDS,
        SECTOR_MAP, CIN_MAP, BSE_MAP,
        get_ticker, get_sector, get_ir_urls, get_cin, get_bse_code,
        list_companies_by_sector, list_all_sectors,
    )
"""

from .company_loader import load_company, CompanyDataError
from .pdf_scraper import scrape_pdfs
from .mca_scraper import scrape_mca_bse
from .yahoo_scraper import fetch_yahoo_data, fetch_multiple_companies, YahooDataError
from .runner import run_ingestion_pipeline, IngestionResult
from .s3_uploader import upload_to_s3, S3UploadError, object_exists
from .companies import (
    COMPANIES, COMPANY_MAP, ALL_COMPANY_IDS,
    SECTOR_MAP, CIN_MAP, BSE_MAP,
    get_ticker, get_sector, get_ir_urls, get_cin, get_bse_code,
    list_companies_by_sector, list_all_sectors,
)

__all__ = [
    # Loaders
    "load_company", "CompanyDataError",
    # Scrapers
    "scrape_pdfs", "scrape_mca_bse",
    "fetch_yahoo_data", "fetch_multiple_companies", "YahooDataError",
    # Pipeline
    "run_ingestion_pipeline", "IngestionResult",
    # S3
    "upload_to_s3", "S3UploadError", "object_exists",
    # Company config
    "COMPANIES", "COMPANY_MAP", "ALL_COMPANY_IDS",
    "SECTOR_MAP", "CIN_MAP", "BSE_MAP",
    "get_ticker", "get_sector", "get_ir_urls", "get_cin", "get_bse_code",
    "list_companies_by_sector", "list_all_sectors",
]