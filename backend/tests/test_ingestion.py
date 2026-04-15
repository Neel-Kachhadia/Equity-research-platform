"""
STEP 4: TEST — Module 1: Data Ingestion & Storage

How to run:
    cd backend/
    python -m tests.test_ingestion

Expected output (success):
    [DB INIT] Tables created.
    [TEST] Uploading: sample_report.pdf → RELIANCE/2024/annual_report.pdf
    [RESULT] {
        "status": "success",
        "s3_key": "RELIANCE/2024/annual_report.pdf",
        "db_row_id": 1,
        "error": null
    }

Expected output (file not found):
    [RESULT] {
        "status": "failed",
        "s3_key": null,
        "db_row_id": null,
        "error": "File not found: ghost.pdf"
    }
"""

import json
import os
import sys

# Allow running from backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.database import init_db
from modules.ingestion.ingestion import ingest_document


def test_successful_upload():
    """Happy path: upload a real PDF to S3."""
    # ── Change this to a real PDF path on your machine ──
    file_path = "tests/sample_report.pdf"

    result = ingest_document(
        file_path=file_path,
        company_id="RELIANCE",
        year="2024",
        doc_type="annual_report",
    )
    print(f"[TEST: success path]\n{json.dumps(result, indent=2)}\n")


def test_file_not_found():
    """Should return a clean error without crashing."""
    result = ingest_document(
        file_path="ghost.pdf",
        company_id="INFOSYS",
        year="2023",
        doc_type="annual_report",
    )
    print(f"[TEST: file not found]\n{json.dumps(result, indent=2)}\n")


def test_non_pdf_file():
    """Should reject non-PDF files before touching AWS."""
    result = ingest_document(
        file_path="tests/test_ingestion.py",   # this file itself
        company_id="TCS",
        year="2024",
        doc_type="annual_report",
    )
    print(f"[TEST: non-PDF rejection]\n{json.dumps(result, indent=2)}\n")


if __name__ == "__main__":
    print("[DB INIT] Initialising SQLite...")
    init_db()
    print("[DB INIT] Tables ready.\n")

    test_file_not_found()
    test_non_pdf_file()

    # Only run this if you have AWS creds + a real PDF:
    # test_successful_upload()
