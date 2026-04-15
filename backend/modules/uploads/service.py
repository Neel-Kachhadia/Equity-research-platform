"""
modules/uploads/service.py

S3 presigned-URL upload service for Erebus.
All AWS interaction is isolated here — routes stay thin.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import settings

logger = logging.getLogger(__name__)

# ── Allowed MIME types ────────────────────────────────────────────────────────
ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/json",
}

# Maximum size that the backend *validates* before issuing a presigned URL.
# S3 itself enforces this if you include a content-length-range condition.
MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB

# Presigned URL lifetimes
UPLOAD_URL_TTL   = int(os.getenv("PRESIGNED_UPLOAD_TTL",   "300"))   # 5 minutes
DOWNLOAD_URL_TTL = int(os.getenv("PRESIGNED_DOWNLOAD_TTL", "3600"))  # 1 hour


# ── Result dataclasses ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PresignedUploadResult:
    upload_url: str       # PUT here from frontend
    file_key:   str       # S3 object key
    file_url:   str       # canonical public URL (if bucket is public)
    fields:     dict      # always {} for PUT-based uploads (reserved for POST)


@dataclass(frozen=True)
class PresignedDownloadResult:
    download_url: str     # time-limited GET URL
    file_key:     str
    expires_in:   int     # seconds


# ── S3 client (lazy singleton) ────────────────────────────────────────────────
_s3_client = None


def _get_s3_client():
    """
    Return a cached boto3 S3 client.
    Uses path-style requests so presigned URLs work with any region without
    needing special endpoint handling in the frontend.
    """
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    if not settings.aws.is_configured:
        raise RuntimeError(
            "AWS credentials are not configured. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your environment."
        )

    _s3_client = boto3.client(
        "s3",
        aws_access_key_id     = settings.aws.access_key_id,
        aws_secret_access_key = settings.aws.secret_access_key,
        region_name           = settings.aws.region,
        config                = Config(
            signature_version = "s3v4",
            # Use virtual-hosted style: bucket.s3.region.amazonaws.com
            # Path-style causes a 301 redirect which strips CORS headers
            # and breaks browser PUT uploads.
            s3 = {"addressing_style": "virtual"},
        ),
    )
    logger.info("S3 client initialised (region=%s)", settings.aws.region)
    return _s3_client


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_file_key(prefix: str, original_name: str) -> str:
    """
    Construct a collision-proof S3 key.
    Format:  {prefix}/{uuid}{.ext}
    Example: uploads/2024/04/b3f8a1c2-….pdf
    """
    from datetime import datetime
    _, ext = os.path.splitext(original_name)
    ext = ext.lower().lstrip(".")
    date_path = datetime.utcnow().strftime("%Y/%m")
    unique_id = uuid.uuid4().hex
    key = f"{prefix.rstrip('/')}/{date_path}/{unique_id}"
    if ext:
        key = f"{key}.{ext}"
    return key


def _canonical_url(file_key: str) -> str:
    """Build the direct (non-presigned) S3 URL for a file key."""
    bucket = settings.aws.s3_bucket_name
    region = settings.aws.region
    return f"https://{bucket}.s3.{region}.amazonaws.com/{file_key}"


def _validate_mime(content_type: str) -> None:
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"File type '{content_type}' is not allowed. "
            f"Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
        )


def _validate_filename(file_name: str) -> None:
    if not file_name or len(file_name.strip()) == 0:
        raise ValueError("file_name must not be empty.")
    if len(file_name) > 255:
        raise ValueError("file_name must be at most 255 characters.")
    # Strip path traversal attempts
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- (),&'[]@+=#!~")
    base = os.path.basename(file_name)
    if not all(c in safe_chars for c in base):
        raise ValueError("file_name contains invalid characters.")


# ── Public API ────────────────────────────────────────────────────────────────

def generate_upload_url(
    file_name:    str,
    content_type: str,
    prefix:       str = "uploads",
    metadata:     Optional[dict] = None,
) -> PresignedUploadResult:
    """
    Generate a presigned S3 PUT URL.

    The frontend uploads the file directly to S3 using an HTTP PUT with:
      - Header: Content-Type: <content_type>
      - Body:   raw file bytes

    Args:
        file_name:    Original file name (used only for extension).
        content_type: MIME type (validated against allowlist).
        prefix:       S3 key prefix / "folder" (default: "uploads").
        metadata:     Optional dict of S3 object metadata (x-amz-meta-*).

    Returns:
        PresignedUploadResult with upload_url, file_key, file_url.

    Raises:
        ValueError:   Validation failure.
        RuntimeError: AWS not configured.
        ClientError:  boto3 S3 error.
    """
    _validate_filename(file_name)
    _validate_mime(content_type)

    file_key = _build_file_key(prefix, file_name)
    file_url = _canonical_url(file_key)

    params: dict = {
        "Bucket":      settings.aws.s3_bucket_name,
        "Key":         file_key,
        "ContentType": content_type,
    }
    if metadata:
        params["Metadata"] = {k: str(v) for k, v in metadata.items()}

    try:
        s3 = _get_s3_client()
        upload_url = s3.generate_presigned_url(
            ClientMethod   = "put_object",
            Params         = params,
            ExpiresIn      = UPLOAD_URL_TTL,
            HttpMethod     = "PUT",
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("Failed to generate presigned upload URL: %s", exc)
        raise

    logger.info("Presigned upload URL generated: key=%s ttl=%ds", file_key, UPLOAD_URL_TTL)
    return PresignedUploadResult(
        upload_url = upload_url,
        file_key   = file_key,
        file_url   = file_url,
        fields     = {},
    )


def generate_download_url(file_key: str) -> PresignedDownloadResult:
    """
    Generate a presigned S3 GET URL for private file access.

    Args:
        file_key: The S3 object key returned during upload.

    Returns:
        PresignedDownloadResult with a time-limited download_url.

    Raises:
        RuntimeError: AWS not configured.
        ClientError:  boto3 S3 error (e.g. object not found).
    """
    if not file_key or ".." in file_key:
        raise ValueError("Invalid file_key.")

    try:
        s3 = _get_s3_client()

        # Verify object exists before issuing URL (avoids silent 404s)
        s3.head_object(Bucket=settings.aws.s3_bucket_name, Key=file_key)

        download_url = s3.generate_presigned_url(
            ClientMethod = "get_object",
            Params       = {
                "Bucket": settings.aws.s3_bucket_name,
                "Key":    file_key,
            },
            ExpiresIn    = DOWNLOAD_URL_TTL,
            HttpMethod   = "GET",
        )
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise FileNotFoundError(f"File not found in S3: {file_key}") from exc
        logger.error("S3 ClientError generating download URL: %s", exc)
        raise
    except BotoCoreError as exc:
        logger.error("BotoCoreError generating download URL: %s", exc)
        raise

    logger.info("Presigned download URL generated: key=%s ttl=%ds", file_key, DOWNLOAD_URL_TTL)
    return PresignedDownloadResult(
        download_url = download_url,
        file_key     = file_key,
        expires_in   = DOWNLOAD_URL_TTL,
    )


def delete_file(file_key: str) -> bool:
    """
    Delete an object from S3.

    Returns True on success, False if already absent.
    Raises ClientError for unexpected S3 errors.
    """
    if not file_key or ".." in file_key:
        raise ValueError("Invalid file_key.")

    try:
        s3 = _get_s3_client()
        s3.delete_object(Bucket=settings.aws.s3_bucket_name, Key=file_key)
        logger.info("Deleted S3 object: key=%s", file_key)
        return True
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            return False
        logger.error("S3 ClientError deleting object: %s", exc)
        raise


def list_files(prefix: str = "uploads", max_keys: int = 100) -> list[dict]:
    """
    List objects under a given S3 prefix.
    Returns lightweight dicts — not full metadata — to keep response lean.
    """
    try:
        s3 = _get_s3_client()
        resp = s3.list_objects_v2(
            Bucket  = settings.aws.s3_bucket_name,
            Prefix  = prefix,
            MaxKeys = max_keys,
        )
        return [
            {
                "file_key":      obj["Key"],
                "file_url":      _canonical_url(obj["Key"]),
                "size_bytes":    obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            }
            for obj in resp.get("Contents", [])
        ]
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 error listing objects: %s", exc)
        raise
