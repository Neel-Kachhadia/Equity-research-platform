"""
modules/uploads/schemas.py

Pydantic request/response models for the uploads API.
Keeping schemas separate from service keeps validation logic portable.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


# ── Shared constants ──────────────────────────────────────────────────────────
_ALLOWED_PREFIXES = {"uploads", "reports", "transcripts", "filings", "images", "ocr-uploads"}


# ── Request schemas ───────────────────────────────────────────────────────────

class GenerateUploadUrlRequest(BaseModel):
    """
    Request body for POST /uploads/generate-upload-url
    """
    file_name:    str = Field(
        ...,
        min_length = 1,
        max_length = 255,
        examples   = ["annual_report_fy24.pdf"],
        description = "Original filename including extension."
    )
    file_type:    str = Field(
        ...,
        examples    = ["application/pdf"],
        description = "MIME content type of the file."
    )
    prefix:       str = Field(
        default     = "uploads",
        examples    = ["uploads", "reports"],
        description = "S3 key prefix (logical folder)."
    )
    metadata:     Optional[dict[str, str]] = Field(
        default     = None,
        description = "Optional S3 object metadata (stored as x-amz-meta-*)."
    )

    @field_validator("file_name")
    @classmethod
    def sanitise_filename(cls, v: str) -> str:
        v = v.strip()
        # Reject path traversal
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("file_name must not contain path separators.")
        # Allow: letters, digits, spaces, and common punctuation found in real filenames
        # (commas, apostrophes, brackets, @, +, =, #, etc.)
        if not re.match(r"^[\w\s.\-(),&'\[\]@+=#!~]+$", v):
            raise ValueError("file_name contains invalid characters.")
        return v

    @field_validator("file_type")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        v = v.strip().lower()
        # Coarse format check — service layer does allowlist check
        if "/" not in v or len(v) > 100:
            raise ValueError("file_type must be a valid MIME type (e.g. application/pdf).")
        return v

    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        v = v.strip().lower().strip("/")
        if v not in _ALLOWED_PREFIXES:
            raise ValueError(
                f"prefix must be one of: {', '.join(sorted(_ALLOWED_PREFIXES))}"
            )
        return v

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[dict]) -> Optional[dict]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("metadata may contain at most 10 keys.")
        for key, val in v.items():
            if len(key) > 128 or len(str(val)) > 256:
                raise ValueError("metadata keys/values exceed maximum length.")
        return v


class GenerateDownloadUrlRequest(BaseModel):
    """
    Request body for POST /uploads/generate-download-url
    """
    file_key: str = Field(
        ...,
        min_length  = 1,
        max_length  = 1024,
        examples    = ["uploads/2024/04/b3f8a1c2abc123.pdf"],
        description = "S3 object key returned during upload."
    )

    @field_validator("file_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        v = v.strip()
        if ".." in v:
            raise ValueError("file_key must not contain '..'.")
        return v


class DeleteFileRequest(BaseModel):
    """
    Request body for DELETE /uploads/file
    """
    file_key: str = Field(..., min_length=1, max_length=1024)

    @field_validator("file_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        v = v.strip()
        if ".." in v:
            raise ValueError("file_key must not contain '..'.")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class UploadUrlResponse(BaseModel):
    """
    Response for generate-upload-url.
    Frontend uses upload_url (HTTP PUT) and then stores file_key + file_url.
    """
    upload_url: str = Field(description="Presigned S3 PUT URL — valid for 5 minutes.")
    file_key:   str = Field(description="Unique S3 object key — store this for later access.")
    file_url:   str = Field(description="Canonical S3 URL (use for public buckets).")
    expires_in: int = Field(description="Presigned URL lifetime in seconds.", default=300)
    method:     str = Field(description="HTTP method to use when uploading.", default="PUT")

    model_config = {"json_schema_extra": {
        "example": {
            "upload_url": "https://erebus-documents.s3.ap-south-1.amazonaws.com/uploads/2024/04/b3f8.pdf?...",
            "file_key":   "uploads/2024/04/b3f8a1c2abc123.pdf",
            "file_url":   "https://erebus-documents.s3.ap-south-1.amazonaws.com/uploads/2024/04/b3f8a1c2abc123.pdf",
            "expires_in": 300,
            "method":     "PUT",
        }
    }}


class DownloadUrlResponse(BaseModel):
    """Response for generate-download-url."""
    download_url: str = Field(description="Presigned S3 GET URL.")
    file_key:     str
    expires_in:   int = Field(description="Seconds until the URL expires.")


class DeleteFileResponse(BaseModel):
    """Response for DELETE /uploads/file."""
    deleted:  bool
    file_key: str
    message:  str


class FileListItem(BaseModel):
    file_key:      str
    file_url:      str
    size_bytes:    int
    last_modified: str


class FileListResponse(BaseModel):
    files:  list[FileListItem]
    count:  int
    prefix: str


class ErrorResponse(BaseModel):
    """Standardised error envelope."""
    error:   str
    detail:  Optional[str] = None
    code:    Optional[str] = None
