"""
modules/uploads/router.py

FastAPI router wiring the upload service to HTTP endpoints.

Endpoints
─────────
POST   /uploads/generate-upload-url    → presigned PUT URL for direct S3 upload
POST   /uploads/generate-download-url  → presigned GET URL for private file access
DELETE /uploads/file                   → delete an S3 object
GET    /uploads/files                  → list objects under a prefix
GET    /uploads/health                 → sanity check (AWS connectivity)
"""

from __future__ import annotations

import logging
from botocore.exceptions import BotoCoreError, ClientError

from fastapi import APIRouter, HTTPException, Query, status

from .schemas import (
    GenerateUploadUrlRequest,
    GenerateDownloadUrlRequest,
    DeleteFileRequest,
    UploadUrlResponse,
    DownloadUrlResponse,
    DeleteFileResponse,
    FileListResponse,
    FileListItem,
)
from . import service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["Uploads"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _handle_aws_error(exc: Exception) -> HTTPException:
    """Translate boto3 / service errors into appropriate HTTP responses."""
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, RuntimeError):
        # AWS not configured
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AWS S3 is not configured on this server."
        )
    if isinstance(exc, ClientError):
        code = exc.response["Error"]["Code"]
        msg  = exc.response["Error"]["Message"]
        logger.error("S3 ClientError %s: %s", code, msg)
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 error ({code}): {msg}"
        )
    if isinstance(exc, BotoCoreError):
        logger.error("BotoCoreError: %s", exc)
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AWS connectivity error. Try again shortly."
        )
    logger.exception("Unexpected upload error: %s", exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred."
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/generate-upload-url",
    response_model  = UploadUrlResponse,
    status_code     = status.HTTP_200_OK,
    summary         = "Generate a presigned S3 PUT URL",
    description     = (
        "Returns a short-lived presigned URL the browser can use to upload a "
        "file **directly** to S3 without passing through this server.\n\n"
        "**Frontend flow**:\n"
        "1. POST here to get `upload_url`.\n"
        "2. `PUT <upload_url>` with `Content-Type` header and raw file bytes.\n"
        "3. Store `file_key` (for later private access) and `file_url` "
        "(for immediate public access)."
    ),
)
async def generate_upload_url(body: GenerateUploadUrlRequest) -> UploadUrlResponse:
    try:
        result = service.generate_upload_url(
            file_name    = body.file_name,
            content_type = body.file_type,
            prefix       = body.prefix,
            metadata     = body.metadata,
        )
    except Exception as exc:
        raise _handle_aws_error(exc) from exc

    return UploadUrlResponse(
        upload_url = result.upload_url,
        file_key   = result.file_key,
        file_url   = result.file_url,
        expires_in = service.UPLOAD_URL_TTL,
        method     = "PUT",
    )


@router.post(
    "/generate-download-url",
    response_model  = DownloadUrlResponse,
    status_code     = status.HTTP_200_OK,
    summary         = "Generate a presigned S3 GET URL (private access)",
    description     = (
        "Generates a time-limited URL for **private** file access. "
        "Use this when the S3 bucket is not publicly readable.\n\n"
        "The URL expires after 1 hour by default."
    ),
)
async def generate_download_url(body: GenerateDownloadUrlRequest) -> DownloadUrlResponse:
    try:
        result = service.generate_download_url(file_key=body.file_key)
    except Exception as exc:
        raise _handle_aws_error(exc) from exc

    return DownloadUrlResponse(
        download_url = result.download_url,
        file_key     = result.file_key,
        expires_in   = result.expires_in,
    )


@router.delete(
    "/file",
    response_model  = DeleteFileResponse,
    summary         = "Delete an S3 object",
)
async def delete_file(body: DeleteFileRequest) -> DeleteFileResponse:
    try:
        deleted = service.delete_file(file_key=body.file_key)
    except Exception as exc:
        raise _handle_aws_error(exc) from exc

    return DeleteFileResponse(
        deleted  = deleted,
        file_key = body.file_key,
        message  = "File deleted." if deleted else "File was not found (already deleted or never existed).",
    )


@router.get(
    "/files",
    response_model = FileListResponse,
    summary        = "List uploaded files under a prefix",
)
async def list_files(
    prefix:   str = Query(default="uploads", description="S3 key prefix to list."),
    max_keys: int = Query(default=100, ge=1, le=1000, description="Maximum number of results."),
) -> FileListResponse:
    try:
        items = service.list_files(prefix=prefix, max_keys=max_keys)
    except Exception as exc:
        raise _handle_aws_error(exc) from exc

    return FileListResponse(
        files  = [FileListItem(**item) for item in items],
        count  = len(items),
        prefix = prefix,
    )


@router.get(
    "/health",
    summary = "Check AWS S3 connectivity",
    description = "Attempts a lightweight HeadBucket call to verify S3 credentials.",
)
async def uploads_health() -> dict:
    from core.config import settings
    from botocore.exceptions import ClientError as CE

    if not settings.aws.is_configured:
        return {"status": "unconfigured", "message": "AWS credentials not set."}

    try:
        s3 = service._get_s3_client()
        s3.head_bucket(Bucket=settings.aws.s3_bucket_name)
        return {
            "status": "ok",
            "bucket": settings.aws.s3_bucket_name,
            "region": settings.aws.region,
        }
    except CE as exc:
        code = exc.response["Error"]["Code"]
        return {"status": "error", "code": code, "detail": str(exc)}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@router.get(
    "/sources",
    summary="Full S3 research sources grouped by company (Sources Visualization)",
)
async def list_sources(max_keys: int = Query(default=2000, ge=1, le=5000)) -> dict:
    """
    Scans the entire S3 bucket and returns all research documents grouped by company.
    Enriches each company with: sector, file types, total size, chunk count from pgvector.

    Response:
        {
          "companies": [
            {
              "ticker": "TCS",
              "name": "TCS",
              "sector": "IT Services",
              "files": [ { file_key, name, size_bytes, last_modified, file_type } ],
              "pdf_count": 5,
              "data_count": 2,
              "total_bytes": 12345678,
              "chunks_indexed": 324,
              "has_data": true,
            }
          ],
          "totals": { "companies": N, "files": N, "pdfs": N, "total_bytes": N, "chunks": N }
        }
    """
    from core.config import settings as cfg

    try:
        s3        = service._get_s3_client()
        bucket    = cfg.aws.s3_bucket_name
        paginator = s3.get_paginator("list_objects_v2")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"S3 unavailable: {exc}")

    # ── Sector & name map from COMPANIES master ───────────────────────────────
    sector_map: dict = {}
    name_map:   dict = {}
    try:
        from modules.ingestion.companies import COMPANIES
        for c in COMPANIES:
            sector_map[c["id"]] = c.get("sector", "—")
            name_map[c["id"]]   = c.get("name", c["id"])
    except Exception:
        pass

    # ── Scan entire bucket ────────────────────────────────────────────────────
    company_buckets: dict = {}
    SKIP_PREFIXES = {"uploads/"}   # exclude raw user uploads from research view

    for page in paginator.paginate(Bucket=bucket, PaginationConfig={"MaxItems": max_keys}):
        for obj in page.get("Contents", []):
            key      = obj["Key"]
            size     = obj.get("Size", 0)
            modified = obj.get("LastModified")

            # Determine company prefix (first path segment)
            parts  = key.split("/")
            prefix = parts[0] if len(parts) > 1 else "__root__"

            # Skip user-uploaded files not part of the research corpus
            if any(key.startswith(p) for p in SKIP_PREFIXES):
                continue

            # File type classification
            low = key.lower()
            if   low.endswith(".pdf"):          ftype = "PDF"
            elif low.endswith(".xlsx"):         ftype = "EXCEL"
            elif low.endswith(".csv"):          ftype = "CSV"
            elif low.endswith(".json"):         ftype = "JSON"
            elif low.endswith(".txt"):          ftype = "TXT"
            elif low.endswith((".png",".jpg","jpeg",".webp")): ftype = "IMAGE"
            else:                               ftype = "OTHER"

            if prefix not in company_buckets:
                company_buckets[prefix] = {
                    "ticker":      prefix,
                    "name":        name_map.get(prefix, prefix),
                    "sector":      sector_map.get(prefix, "—"),
                    "files":       [],
                    "pdf_count":   0,
                    "data_count":  0,
                    "total_bytes": 0,
                    "chunks_indexed": 0,
                }

            b = company_buckets[prefix]
            b["files"].append({
                "file_key":     key,
                "name":         parts[-1],
                "size_bytes":   size,
                "last_modified": modified.isoformat() if modified else None,
                "file_type":    ftype,
            })
            b["total_bytes"] += size
            if ftype == "PDF":
                b["pdf_count"] += 1
            if ftype in ("EXCEL", "CSV", "JSON"):
                b["data_count"] += 1

    # ── Chunk counts from pgvector per company ────────────────────────────────
    try:
        from core.database import execute_query
        rows = execute_query("""
            SELECT metadata->>'company_id' AS ticker, COUNT(*) AS cnt
            FROM documents
            WHERE metadata->>'company_id' IS NOT NULL
            GROUP BY metadata->>'company_id'
        """)
        for r in rows:
            t = (r.get("ticker") or "").upper()
            if t in company_buckets:
                company_buckets[t]["chunks_indexed"] = int(r["cnt"])
    except Exception as e:
        logger.debug("[sources] pgvector chunk query failed: %s", e)

    # ── Sort by ticker, attach has_data flag ──────────────────────────────────
    companies = sorted(company_buckets.values(), key=lambda x: x["ticker"])
    for c in companies:
        c["has_data"]    = c["data_count"] > 0
        c["has_chunks"]  = c["chunks_indexed"] > 0
        # Sort files by recency within each company
        c["files"].sort(key=lambda f: f["last_modified"] or "", reverse=True)

    totals = {
        "companies":   len(companies),
        "files":       sum(len(c["files"]) for c in companies),
        "pdfs":        sum(c["pdf_count"]  for c in companies),
        "total_bytes": sum(c["total_bytes"] for c in companies),
        "chunks":      sum(c["chunks_indexed"] for c in companies),
    }

    return {"companies": companies, "totals": totals}
