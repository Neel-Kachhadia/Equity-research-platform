"""
Storage utilities for S3 uploads and PostgreSQL metadata management.
"""

import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

import boto3
import botocore.exceptions

from core.config import settings
from core.database import execute_write, execute_single, get_cursor
from core.redis_client import cache_delete, build_document_key, invalidate_company_cache

logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3_client():
    """Build and return a cached boto3 S3 client."""
    global _s3_client
    
    if _s3_client is None:
        if not settings.aws.is_configured:
            raise RuntimeError(
                "AWS credentials not configured. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
            )
        
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws.access_key_id,
            aws_secret_access_key=settings.aws.secret_access_key,
            region_name=settings.aws.region,
        )
        logger.info(f"S3 client initialized for bucket: {settings.aws.s3_bucket_name}")
    
    return _s3_client


def validate_pdf(file_path: str) -> tuple[bool, Optional[str]]:
    """Validate that a file is a legitimate PDF."""
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    if path.suffix.lower() != ".pdf":
        return False, f"Only PDF files are supported, got: {path.suffix}"
    
    try:
        with open(path, 'rb') as f:
            magic_bytes = f.read(4)
            if magic_bytes != b'%PDF':
                return False, f"Invalid PDF file (missing %PDF header): {file_path}"
    except Exception as e:
        return False, f"Failed to read file for validation: {e}"
    
    return True, None


def upload_to_s3(
    file_bytes: bytes, 
    company_id: str, 
    year: str, 
    doc_type: str,
    original_filename: Optional[str] = None
) -> str:
    """Upload raw PDF bytes to S3 with collision prevention."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    company_id_clean = company_id.replace('/', '_').replace('\\', '_')
    doc_type_clean = doc_type.replace('/', '_').replace('\\', '_')
    
    s3_key = f"{company_id_clean}/{year}/{doc_type_clean}_{timestamp}.pdf"
    client = _get_s3_client()

    s3_metadata = {
        'company_id': company_id,
        'year': year,
        'doc_type': doc_type,
        'uploaded_at': datetime.utcnow().isoformat(),
    }
    
    if original_filename:
        s3_metadata['original_filename'] = original_filename

    try:
        client.put_object(
            Bucket=settings.aws.s3_bucket_name,
            Key=s3_key,
            Body=file_bytes,
            ContentType="application/pdf",
            Metadata=s3_metadata
        )
        
        logger.info(f"Successfully uploaded to S3: s3://{settings.aws.s3_bucket_name}/{s3_key}")
        return s3_key

    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = f"S3 upload failed [{error_code}]: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def save_metadata(
    company_id: str,
    year: str,
    doc_type: str,
    s3_path: str,
    status: str = "uploaded",
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
) -> int:
    """
    Insert a document metadata record into PostgreSQL.
    Returns the inserted row ID.
    """
    query = """
        INSERT INTO documents 
            (company_id, year, doc_type, s3_path, status, filename, file_size)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        row_id = execute_write(
            query,
            (company_id, year, doc_type, s3_path, status, filename, file_size),
            returning="id"
        )
        
        invalidate_company_cache(company_id, year)
        
        logger.info(
            f"Saved metadata for {company_id}/{year}/{doc_type} "
            f"(ID: {row_id}, size: {file_size} bytes)"
        )
        return row_id
        
    except Exception as e:
        error_msg = f"Failed to save metadata: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def get_document_metadata(doc_id: int) -> Optional[dict]:
    """Retrieve document metadata by ID."""
    from core.redis_client import cache_get, cache_set
    
    cache_key = build_document_key(doc_id)
    cached = cache_get(cache_key)
    if cached:
        logger.debug(f"Cache hit for document {doc_id}")
        return cached
    
    query = "SELECT * FROM documents WHERE id = %s"
    result = execute_single(query, (doc_id,))
    
    if result:
        cache_set(cache_key, dict(result), ttl=3600)
    
    return dict(result) if result else None


def update_document_status(
    doc_id: int,
    status: str,
    error_message: Optional[str] = None
) -> bool:
    """Update document processing status."""
    try:
        if error_message:
            query = """
                UPDATE documents 
                SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (status, error_message, doc_id)
        else:
            query = """
                UPDATE documents 
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (status, doc_id)
        
        with get_cursor() as cur:
            cur.execute(query, params)
            affected = cur.rowcount
        
        cache_delete(build_document_key(doc_id))
        
        logger.info(f"Updated document {doc_id} status to '{status}'")
        return affected > 0
        
    except Exception as e:
        logger.error(f"Failed to update document status: {e}")
        return False
        #s