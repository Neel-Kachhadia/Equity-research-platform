"""
EREBUS — Ingestion / Companies Router
======================================
GET /companies  →  List all company folders available in the S3 bucket
                   that have at least one parseable data file (.xlsx or .json).

Response:
    {
        "companies": [
            { "ticker": "TCS",     "prefix": "TCS/",     "has_excel": true,  "has_json": false },
            { "ticker": "Infosys", "prefix": "Infosys/", "has_excel": true,  "has_json": false },
            ...
        ],
        "count": 2,
        "bucket": "erebus-data-prod",
        "skipped": ["HCL_TECH"]   # folders that had no parseable data
    }

Companies are ONLY included if they have at least one .xlsx or .json file.
This prevents showing S3 folders that would fail when analysed.
"""

from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["Companies"])

# Extensions that the loader can actually parse
_DATA_EXTENSIONS = (".xlsx", ".json")
# Extensions that are index/document files — not financial data
_SKIP_SUFFIXES   = ("_documents.json",)
# S3 top-level folders that are NOT company tickers
_SYSTEM_PREFIXES = {
    "uploads", "ocr-uploads", "ocr_uploads",
    "tmp", "temp", "backup", "backups", "archive",
    "logs", "cache", "system", "config",
}
# S3 folder names that are NOT companies — filter from scorecard list
_SKIP_PREFIXES   = {
    "uploads", "ocr-uploads", "ocr_uploads", "__root__",
    "__macosx", ".ds_store", "tmp", "temp", "test",
}


@router.get("", summary="List all companies available in S3 with parseable data")
def list_companies():
    """
    Scans the S3 bucket for company folders that contain at least one
    parseable financial data file (.xlsx or .json).

    Folders that exist in S3 but contain ONLY PDFs (or are empty) are
    excluded — they would fail when analysed and should not appear in
    the comparison picker.
    """
    try:
        from modules.ingestion.company_loader import _get_s3_client, _get_bucket

        BUCKET    = _get_bucket()          # read live from env on every request
        client    = _get_s3_client()
        paginator = client.get_paginator("list_objects_v2")

        # ── Step 1: collect ALL objects in the bucket (no delimiter) ──────────
        all_objects: list[dict] = []
        for page in paginator.paginate(Bucket=BUCKET):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                if key:
                    all_objects.append({"key": key, "size": obj.get("Size", 0)})

        # ── Step 2: partition by top-level prefix ─────────────────────────────
        # Key examples:
        #   "TCS/Coforge.xlsx"          → prefix "TCS", file "Coforge.xlsx"
        #   "Infosys/Annual.pdf"        → prefix "Infosys", file "Annual.pdf"
        #   "TCS.xlsx"                  → root-level file, prefix "TCS"
        prefix_files: dict[str, list[str]] = {}  # prefix → list of file keys

        for obj in all_objects:
            key = obj["key"]
            if "/" in key:
                top_prefix = key.split("/")[0]
            else:
                # Root-level file — treat the basename (minus extension) as the company
                if key.lower().endswith(".xlsx"):
                    top_prefix = key[:-5]   # strip .xlsx
                elif key.lower().endswith(".json"):
                    top_prefix = key[:-5]   # strip .json
                else:
                    continue   # skip root-level PDFs
            if top_prefix not in prefix_files:
                prefix_files[top_prefix] = []
            prefix_files[top_prefix].append(key)

        # ── Step 3: include ALL companies that have ANY files ─────────────────
        companies:  list[dict] = []

        for ticker in sorted(prefix_files):
            # Skip system/upload folders that are not company tickers
            if ticker.lower() in _SYSTEM_PREFIXES:
                logger.debug("[companies] Skipping system folder: %s", ticker)
                continue

            # Skip system/utility folders that aren't real companies
            if ticker.lower() in _SKIP_PREFIXES:
                continue

            keys = prefix_files[ticker]

            has_excel = any(k.lower().endswith(".xlsx") for k in keys)
            has_json  = any(
                k.lower().endswith(".json")
                and not k.lower().endswith("_documents.json")
                for k in keys
            )
            has_docs  = any(
                k.lower().endswith(".pdf") or k.lower().endswith("_documents.json")
                for k in keys
            )

            companies.append({
                "ticker":     ticker,
                "prefix":     f"{ticker}/",
                "has_excel":  has_excel,
                "has_json":   has_json,
                "has_docs":   has_docs,
                "file_count": len(keys),
            })

        logger.info(
            "[companies] Listed %d companies from S3 bucket %s",
            len(companies), BUCKET,
        )
        return {
            "companies": companies,
            "count":     len(companies),
            "bucket":    BUCKET,
        }

    except Exception as e:
        logger.error("[companies] Failed to list S3 companies: %s", e)
        raise HTTPException(500, detail=f"Could not list companies from S3: {e}")
