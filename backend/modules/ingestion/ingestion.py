"""
Document ingestion orchestrator with comprehensive error handling and logging.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from modules.ingestion.storage import (
    upload_to_s3,
    save_metadata,
    validate_pdf,
)

logger = logging.getLogger(__name__)


def ingest_document(
    file_path: str,
    company_id: str,
    year: str,
    doc_type: str,
) -> dict:
    """
    Orchestrator for Module 1: Data Ingestion & Storage.

    Steps:
        1. Validate the file exists and is a valid PDF.
        2. Get file metadata (size) before reading.
        3. Read file bytes with error handling.
        4. Upload to S3.
        5. Save metadata to PostgreSQL.
        6. Return a result dict with status and S3 key.

    Args:
        file_path:  Local path to the PDF file.
        company_id: Company identifier (e.g. "RELIANCE").
        year:       Fiscal year string (e.g. "2024").
        doc_type:   Type of document (e.g. "annual_report", "earnings_transcript").

    Returns:
        {
            "status":    "success" | "failed" | "partial_success",
            "s3_key":    "<s3_key>" | None,
            "db_row_id": <int> | None,
            "error":     None | "<error message>",
        }
    """
    start_time = datetime.utcnow()
    logger.info(f"Starting ingestion: {file_path} for {company_id}/{year}/{doc_type}")
    
    is_valid, error_msg = validate_pdf(file_path)
    if not is_valid:
        logger.error(f"PDF validation failed: {error_msg}")
        return _error_result(error_msg)
    
    path = Path(file_path)
    filename = path.name
    
    try:
        file_size = path.stat().st_size
        logger.info(f"File validated: {filename} ({file_size} bytes)")
    except OSError as e:
        error_msg = f"Cannot access file metadata: {file_path}"
        logger.error(f"{error_msg}: {e}")
        return _error_result(error_msg)
    
    try:
        file_bytes = path.read_bytes()
        logger.info(f"Successfully read {file_size} bytes from {file_path}")
    except PermissionError as e:
        error_msg = f"Permission denied reading file: {file_path}"
        logger.error(f"{error_msg}: {e}")
        return _error_result(error_msg)
    except IOError as e:
        error_msg = f"I/O error reading file: {file_path}"
        logger.error(f"{error_msg}: {e}")
        return _error_result(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error reading file: {file_path}"
        logger.exception(error_msg)
        return _error_result(f"{error_msg}: {str(e)}")

    s3_key = None
    try:
        s3_key = upload_to_s3(
            file_bytes=file_bytes,
            company_id=company_id,
            year=year,
            doc_type=doc_type,
            original_filename=filename
        )
        logger.info(f"Uploaded to S3: {s3_key}")
        
    except RuntimeError as e:
        logger.error(f"S3 upload failed: {e}")
        try:
            row_id = save_metadata(
                company_id=company_id,
                year=year,
                doc_type=doc_type,
                s3_path="",
                status="failed",
                filename=filename,
                file_size=file_size
            )
            logger.info(f"Recorded failed upload attempt (ID: {row_id}, size: {file_size} bytes)")
        except Exception as db_error:
            logger.error(f"Failed to save failure metadata: {db_error}")
        
        return _error_result(str(e))

    try:
        row_id = save_metadata(
            company_id=company_id,
            year=year,
            doc_type=doc_type,
            s3_path=s3_key,
            status="uploaded",
            filename=filename,
            file_size=file_size
        )
        logger.info(f"Saved metadata to database (ID: {row_id})")
        
    except RuntimeError as e:
        error_msg = f"METADATA SAVE FAILED after successful S3 upload: {e}"
        logger.critical(f"{error_msg}. S3 key: {s3_key}")
        
        return {
            "status": "partial_success",
            "s3_key": s3_key,
            "db_row_id": None,
            "error": f"Uploaded to S3 but metadata save failed: {str(e)}",
            "filename": filename,
            "file_size_bytes": file_size,
        }

    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Ingestion completed successfully in {duration:.2f}s "
        f"(ID: {row_id}, S3: {s3_key})"
    )
    
    return {
        "status": "success",
        "s3_key": s3_key,
        "db_row_id": row_id,
        "error": None,
        "filename": filename,
        "file_size_bytes": file_size,
        "duration_seconds": duration,
    }


def _error_result(message: str) -> dict:
    return {
        "status": "failed",
        "s3_key": None,
        "db_row_id": None,
        "error": message,
    }
    #s