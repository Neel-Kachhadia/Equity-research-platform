"""
modules/ocr/service.py

OCR pipeline — Tesseract (local, free, no API key required).
S3 → download bytes → preprocess → Tesseract OCR → PostgreSQL

Processing strategy
───────────────────
  JPEG / PNG  →  PIL Image → preprocess → pytesseract.image_to_string()
  PDF         →  pdf2image renders at 300 DPI → preprocess each page → Tesseract

All bytes are held in-memory; nothing is written to disk.
"""

from __future__ import annotations

import io
import json
import logging
import os
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import settings
from core.database import execute_query, execute_single, execute_write, get_cursor

logger = logging.getLogger(__name__)

# ── Tesseract binary path ──────────────────────────────────────────────────────
# On macOS with Homebrew, tesseract lands in /opt/homebrew/bin which may not
# be on PATH when the server starts. Set TESSERACT_CMD in .env to override.
_TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if not _TESSERACT_CMD:
    if os.name == 'nt':
        _TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    else:
        _TESSERACT_CMD = "/opt/homebrew/bin/tesseract"

try:
    import pytesseract as _pt
    _pt.pytesseract.tesseract_cmd = _TESSERACT_CMD
except ImportError:
    pass  # surfaced clearly at call-time

# Tesseract config flags applied to every OCR call:
#   --oem 3   → LSTM neural net engine (best accuracy)
#   --psm 6   → uniform block of text  (ideal for printed / scanned docs)
#   --dpi 300 → tell Tesseract the effective resolution
_TESS_CONFIG = "--oem 3 --psm 6 --dpi 300"

# ── Supported MIME types ────────────────────────────────────────────────────────
OCR_ALLOWED_MIME = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/pdf",
}

# ── Lazy S3 client ─────────────────────────────────────────────────────────────
_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client
    if not settings.aws.is_configured:
        raise RuntimeError("AWS credentials are not configured.")
    _s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.aws.access_key_id,
        aws_secret_access_key=settings.aws.secret_access_key,
        region_name=settings.aws.region,
        config=Config(signature_version="s3v4"),
    )
    return _s3_client


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _canonical_s3_url(s3_key: str) -> str:
    return (
        f"https://{settings.aws.s3_bucket_name}"
        f".s3.{settings.aws.region}.amazonaws.com/{s3_key}"
    )


def _mark_processing(doc_id: int) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE ocr_documents
               SET status = 'processing',
                   processing_started_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = %s
            """,
            (doc_id,),
        )


def _mark_completed(doc_id: int) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE ocr_documents
               SET status = 'completed',
                   processing_completed_at = CURRENT_TIMESTAMP,
                   error_message = NULL,
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = %s
            """,
            (doc_id,),
        )


def _mark_failed(doc_id: int, reason: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE ocr_documents
               SET status = 'failed',
                   processing_completed_at = CURRENT_TIMESTAMP,
                   error_message = %s,
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = %s
            """,
            (reason[:1000], doc_id),
        )


# ── S3 download ────────────────────────────────────────────────────────────────

def _download_s3_bytes(bucket: str, key: str) -> bytes:
    try:
        obj = _get_s3_client().get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        raise RuntimeError(f"S3 download failed ({code}): {key}") from exc
    except BotoCoreError as exc:
        raise RuntimeError(f"S3 connectivity error: {exc}") from exc


# ── Image preprocessing ────────────────────────────────────────────────────────

def _preprocess_for_ocr(image):
    """
    Preprocessing pipeline that significantly improves Tesseract accuracy
    on scanned / photographed documents (no additional dependencies needed).

    Steps
    ─────
    1. Grayscale         — removes colour noise that confuses OCR
    2. Upscale           — ensures effective resolution ≥ 300 DPI (width ≥ 2000 px)
    3. Otsu binarization — adaptive black/white threshold via numpy histogram
    4. Contrast boost    — ImageEnhance.Contrast(1.8)
    5. Sharpen           — ImageFilter.SHARPEN
    """
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np

    # 1. Grayscale
    if image.mode != "L":
        image = image.convert("L")

    # 2. Upscale if width < 2000 px (roughly 300 DPI on A4 paper)
    w, h = image.size
    if w < 2000:
        scale = max(2, 2000 // w)
        image = image.resize((w * scale, h * scale), Image.LANCZOS)

    # 3. Otsu's optimal binarization threshold (computed via numpy histogram)
    arr      = np.array(image, dtype=np.uint8)
    counts   = np.bincount(arr.flatten(), minlength=256)
    total    = arr.size
    s2_total = int((counts * np.arange(256)).sum())
    w1 = s1 = 0
    best_thresh, best_var = 0, 0.0
    for t in range(256):
        n   = int(counts[t])
        w1 += n
        w2  = total - w1
        if w1 == 0 or w2 == 0:
            continue
        s1   += t * n
        s2    = s2_total - s1
        mu1   = s1 / w1
        mu2   = s2 / w2
        var   = w1 * w2 * (mu1 - mu2) ** 2
        if var > best_var:
            best_var, best_thresh = var, t

    image = image.point(lambda px: 255 if px > best_thresh else 0, "L")

    # 4. Contrast boost
    image = ImageEnhance.Contrast(image).enhance(1.8)

    # 5. Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    return image


# ── Tesseract OCR helpers ──────────────────────────────────────────────────────

def _tesseract_ocr_pil(image) -> str:
    """Preprocess a PIL Image and run Tesseract. Returns stripped text."""
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "pytesseract is not installed. Run: pip install pytesseract"
        ) from exc

    processed = _preprocess_for_ocr(image)
    text = pytesseract.image_to_string(processed, config=_TESS_CONFIG)
    return text.strip()


def _ocr_image_bytes(image_bytes: bytes) -> str:
    """Open raw image bytes as PIL Image and run Tesseract with preprocessing."""
    from PIL import Image
    image = Image.open(io.BytesIO(image_bytes))
    return _tesseract_ocr_pil(image)


def _ocr_pdf_bytes(pdf_bytes: bytes) -> dict[int, str]:
    """
    Render each PDF page at 300 DPI → preprocess → Tesseract.
    Returns {page_number: text}.
    """
    try:
        from pdf2image import convert_from_bytes
    except ImportError as exc:
        raise RuntimeError(
            "pdf2image is not installed. Run: pip install pdf2image "
            "(also requires: brew install poppler)"
        ) from exc

    # 300 DPI: major accuracy improvement over the previous 200 DPI
    poppler_kwargs = {}
    if os.getenv("POPPLER_PATH"):
        poppler_kwargs["poppler_path"] = os.getenv("POPPLER_PATH")
    elif os.name == 'nt':
        default_poppler = r"C:\Users\Neel\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"
        if os.path.exists(default_poppler):
            poppler_kwargs["poppler_path"] = default_poppler
            
    images = convert_from_bytes(pdf_bytes, dpi=300, **poppler_kwargs)
    page_texts: dict[int, str] = {}
    for i, image in enumerate(images, start=1):
        page_texts[i] = _tesseract_ocr_pil(image)
        logger.debug("Tesseract OCR page %d/%d done", i, len(images))

    return page_texts


def _save_ocr_result(
    doc_id:         int,
    extracted_text: str,
    raw_response:   dict,
    page_texts:     dict[int, str],
    confidence_avg: Optional[float] = None,
) -> None:
    page_count = len(page_texts) if page_texts else 1
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO ocr_results
                (document_id, textract_job_id, extracted_text,
                 raw_response_json, page_count, confidence_avg)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (doc_id, None, extracted_text, json.dumps(raw_response), page_count, confidence_avg),
        )
        for page_num, page_text in page_texts.items():
            cur.execute(
                """
                INSERT INTO ocr_result_pages (document_id, page_number, page_text)
                VALUES (%s, %s, %s)
                """,
                (doc_id, page_num, page_text),
            )
    logger.info("OCR result saved: doc_id=%s pages=%s", doc_id, page_count)


# ── Main processing entry-point ────────────────────────────────────────────────

def process_document_sync(doc_id: int) -> None:
    """
    Download from S3 and run Tesseract OCR.
    Called from the router's BackgroundTasks thread.
    All bytes are in-memory; nothing written to disk.
    """
    doc = get_document(doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    mime_type = doc.get("mime_type", "")
    if mime_type not in OCR_ALLOWED_MIME:
        raise ValueError(f"Unsupported MIME type: {mime_type}")

    _mark_processing(doc_id)

    try:
        file_bytes = _download_s3_bytes(doc["s3_bucket"], doc["s3_key"])

        if mime_type in ("image/jpeg", "image/jpg", "image/png"):
            text       = _ocr_image_bytes(file_bytes)
            page_texts = {1: text}
            raw        = {"provider": "tesseract", "pages": 1, "mime": mime_type}

        elif mime_type == "application/pdf":
            page_texts = _ocr_pdf_bytes(file_bytes)
            separator  = "\n\n--- Page Break ---\n\n"
            text       = separator.join(page_texts[p] for p in sorted(page_texts))
            raw        = {"provider": "tesseract", "pages": len(page_texts), "mime": mime_type}

        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

        _save_ocr_result(doc_id, text, raw, page_texts)
        _mark_completed(doc_id)
        logger.info("Tesseract OCR completed: doc_id=%s chars=%s", doc_id, len(text))

    except Exception as exc:
        reason = str(exc)
        logger.error("OCR failed doc_id=%s: %s", doc_id, reason)
        _mark_failed(doc_id, reason)
        raise


# ── Registration + read queries (unchanged) ────────────────────────────────────

def register_document(
    file_name: str,
    s3_key:    str,
    mime_type: str,
    file_size: Optional[int] = None,
) -> int:
    if mime_type not in OCR_ALLOWED_MIME:
        raise ValueError(
            f"Unsupported file type '{mime_type}'. "
            f"Allowed: {', '.join(sorted(OCR_ALLOWED_MIME))}"
        )
    s3_url = _canonical_s3_url(s3_key)
    doc_id = execute_write(
        """
        INSERT INTO ocr_documents
            (file_name, s3_bucket, s3_key, s3_url, mime_type, file_size, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'uploaded')
        RETURNING id
        """,
        (file_name, settings.aws.s3_bucket_name, s3_key, s3_url, mime_type, file_size),
    )
    logger.info("OCR document registered: id=%s key=%s", doc_id, s3_key)
    return doc_id


def get_document(doc_id: int) -> Optional[dict]:
    return execute_single("SELECT * FROM ocr_documents WHERE id = %s", (doc_id,))


def get_result(doc_id: int) -> Optional[dict]:
    result = execute_single(
        "SELECT * FROM ocr_results WHERE document_id = %s ORDER BY created_at DESC LIMIT 1",
        (doc_id,),
    )
    if not result:
        return None
    pages = execute_query(
        "SELECT page_number, page_text FROM ocr_result_pages WHERE document_id = %s ORDER BY page_number",
        (doc_id,),
    )
    result = dict(result)
    result["pages"] = [dict(p) for p in pages]
    return result


def list_documents(page: int = 1, limit: int = 20) -> tuple[list, int]:
    offset = (page - 1) * limit
    rows = execute_query(
        """
        SELECT d.id, d.file_name, d.s3_key, d.mime_type, d.file_size, d.status,
               r.page_count, d.upload_created_at, d.processing_completed_at
          FROM ocr_documents d
          LEFT JOIN ocr_results r ON r.document_id = d.id
         ORDER BY d.created_at DESC
         LIMIT %s OFFSET %s
        """,
        (limit, offset),
    )
    total_row = execute_single("SELECT COUNT(*) AS cnt FROM ocr_documents")
    total = total_row["cnt"] if total_row else 0
    return [dict(r) for r in rows], total


def check_ocr_health() -> dict:
    """Check that Tesseract is installed and reachable."""
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        return {"status": "ok", "provider": "tesseract", "version": str(version)}
    except Exception as exc:
        return {"status": "error", "provider": "tesseract", "message": str(exc)}
