"""
EREBUS · S3 Uploader
=====================
Centralized S3 upload functionality.
"""

import os
import logging
import threading
from typing import Optional, Dict, Any

import boto3
import botocore.exceptions
from botocore.config import Config

logger = logging.getLogger(__name__)

# Resolved lazily inside _get_s3_client() so dotenv has time to load first
_BUCKET: str = ""
_REGION: str = ""

_s3_client = None
_s3_lock = threading.Lock()


class S3UploadError(Exception):
    """Raised when S3 upload fails."""
    pass


def _get_s3_client():
    """Thread-safe S3 client getter. Reads env lazily so dotenv loads first."""
    global _s3_client, _BUCKET, _REGION

    if _s3_client is not None:
        return _s3_client

    with _s3_lock:
        if _s3_client is not None:
            return _s3_client

        # Resolve config now (after dotenv has been loaded by the caller)
        _BUCKET = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_S3_BUCKET") or "erebus-data-prod"
        _REGION = os.getenv("AWS_REGION", "ap-south-1")

        aws_key    = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not (aws_key and aws_secret):
            raise S3UploadError(
                "AWS credentials not configured. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
            )

        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=_REGION,
            config=Config(
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=5,
                read_timeout=30,
            ),
        )
        logger.info("[S3] Client initialized (bucket=%s, region=%s)", _BUCKET, _REGION)

    return _s3_client


def upload_to_s3(
    key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    metadata: Optional[Dict[str, str]] = None,
    bucket: Optional[str] = None,
) -> str:
    """
    Upload content to S3.
    
    Args:
        key: S3 object key
        content: Bytes to upload
        content_type: MIME type
        metadata: Optional metadata dict
        bucket: Override bucket (default from env)
        
    Returns:
        Full S3 URI
        
    Raises:
        S3UploadError on failure
    """
    bucket = bucket or _BUCKET
    client = _get_s3_client()
    
    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata or {},
        )
        
        logger.info("[S3] Uploaded: s3://%s/%s (%d bytes)", bucket, key, len(content))
        return f"s3://{bucket}/{key}"
        
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise S3UploadError(f"S3 upload failed [{error_code}]: {key}") from e
    except Exception as e:
        raise S3UploadError(f"S3 upload failed: {key}") from e


def list_objects(prefix: str) -> list:
    """List objects under an S3 prefix."""
    client = _get_s3_client()
    paginator = client.get_paginator("list_objects_v2")
    objects = []
    
    try:
        for page in paginator.paginate(Bucket=_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "modified": obj["LastModified"].isoformat(),
                })
    except botocore.exceptions.ClientError as e:
        logger.warning("[S3] List failed: %s", e)
    
    return objects


def object_exists(key: str) -> bool:
    """Check if object exists in S3."""
    client = _get_s3_client()
    try:
        client.head_object(Bucket=_BUCKET, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise