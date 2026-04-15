"""
modules/ocr/schemas.py

Pydantic request/response schemas for the OCR API.
Mirrors the style of modules/uploads/schemas.py.
"""

from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class RegisterDocumentRequest(BaseModel):
    """
    Register an S3 file for OCR processing.
    Called immediately after the frontend completes the S3 PUT upload.
    """
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original file name including extension.",
        examples=["invoice_march_2024.pdf"],
    )
    s3_key: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="S3 object key returned by the presigned upload endpoint.",
        examples=["ocr-uploads/2024/04/abc123.pdf"],
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the uploaded file.",
        examples=["application/pdf", "image/jpeg"],
    )
    file_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="File size in bytes.",
    )


# ── Response schemas ───────────────────────────────────────────────────────────

class OcrPageResult(BaseModel):
    """Single page result within an OCR response."""
    page_number: int
    page_text: str


class OcrDocumentResponse(BaseModel):
    """Full document metadata + status."""
    id: int
    file_name: str
    s3_bucket: str
    s3_key: str
    s3_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    upload_created_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OcrResultResponse(BaseModel):
    """Extracted text and metadata from a completed OCR run."""
    document_id: int
    textract_job_id: Optional[str] = None
    extracted_text: Optional[str] = None
    page_count: int = 1
    confidence_avg: Optional[float] = None
    pages: List[OcrPageResult] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class OcrDocumentWithResult(BaseModel):
    """Combined document + result for the detail view."""
    document: OcrDocumentResponse
    result: Optional[OcrResultResponse] = None


class OcrHistoryItem(BaseModel):
    """Lightweight row for the history table."""
    id: int
    file_name: str
    s3_key: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    page_count: Optional[int] = None
    upload_created_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


class OcrHistoryResponse(BaseModel):
    """Paginated OCR document history."""
    items: List[OcrHistoryItem]
    total: int
    page: int
    limit: int


class OcrProcessResponse(BaseModel):
    """Response from the process endpoint."""
    document_id: int
    status: str
    message: str


class OcrHealthResponse(BaseModel):
    """Textract health-check response."""
    status: str
    region: Optional[str] = None
    message: Optional[str] = None
