"""
modules/ocr/router.py

FastAPI router for the OCR pipeline (Google Vision backend).

Endpoints
─────────
POST  /ocr/register              → Register S3 file, create ocr_documents row
POST  /ocr/{document_id}/process → Start OCR (background thread, frontend polls)
POST  /ocr/{document_id}/analyze → Run LLM analysis on extracted OCR text
GET   /ocr/{document_id}         → Document metadata + status
GET   /ocr/{document_id}/result  → Extracted text + pages
GET   /ocr/history               → Paginated OCR document history
GET   /ocr/health                → Google Vision connectivity check
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks

from .schemas import (
    RegisterDocumentRequest,
    OcrDocumentResponse,
    OcrResultResponse,
    OcrDocumentWithResult,
    OcrHistoryResponse,
    OcrHistoryItem,
    OcrPageResult,
    OcrProcessResponse,
    OcrHealthResponse,
)
from . import service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["OCR"])

# Thread pool — Google Vision is synchronous but we still run it off the event loop
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr-worker")


# ── Error helper ───────────────────────────────────────────────────────────────

def _handle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    logger.exception("Unexpected OCR error: %s", exc)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Internal error: {exc}",
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=OcrDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an uploaded S3 file for OCR",
    description=(
        "Call this immediately after the browser completes the S3 PUT upload. "
        "Creates an `ocr_documents` record with `status=uploaded`. "
        "Then call `POST /ocr/{id}/process` to kick off Google Vision OCR."
    ),
)
async def register_document(body: RegisterDocumentRequest) -> OcrDocumentResponse:
    try:
        doc_id = service.register_document(
            file_name=body.file_name,
            s3_key=body.s3_key,
            mime_type=body.mime_type,
            file_size=body.file_size,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=500, detail="Document created but could not be retrieved.")
    return OcrDocumentResponse(**dict(doc))


@router.post(
    "/{document_id}/process",
    response_model=OcrProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start OCR processing on a registered document",
    description=(
        "Kicks off Google Vision OCR. Returns 202 immediately. "
        "OCR runs in a background thread (synchronous Vision API call). "
        "Poll `GET /ocr/{id}` until status is `completed` or `failed`."
    ),
)
async def process_document(document_id: int, background_tasks: BackgroundTasks) -> OcrProcessResponse:
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found.")

    if doc["status"] in ("processing",):
        return OcrProcessResponse(
            document_id=document_id,
            status="processing",
            message="OCR is already running for this document.",
        )

    # Run in background thread — won't block the event loop
    loop = asyncio.get_event_loop()
    background_tasks.add_task(
        _run_in_thread, loop, document_id
    )

    return OcrProcessResponse(
        document_id=document_id,
        status="processing",
        message="OCR started. Poll GET /ocr/{id} for status updates.",
    )


def _run_in_thread(loop: asyncio.AbstractEventLoop, document_id: int) -> None:
    """Delegate OCR work to thread pool so the event loop stays free."""
    try:
        service.process_document_sync(document_id)
    except Exception as exc:
        logger.error("Background OCR thread failed for doc_id=%s: %s", document_id, exc)


@router.get(
    "/history",
    response_model=OcrHistoryResponse,
    summary="List all OCR documents with pagination",
)
async def list_history(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page."),
) -> OcrHistoryResponse:
    try:
        rows, total = service.list_documents(page=page, limit=limit)
    except Exception as exc:
        raise _handle_error(exc) from exc

    items = [OcrHistoryItem(**r) for r in rows]
    return OcrHistoryResponse(items=items, total=total, page=page, limit=limit)


@router.get(
    "/{document_id}",
    response_model=OcrDocumentResponse,
    summary="Get document metadata and processing status",
)
async def get_document(document_id: int) -> OcrDocumentResponse:
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found.")
    return OcrDocumentResponse(**dict(doc))


@router.get(
    "/{document_id}/result",
    response_model=OcrResultResponse,
    summary="Get OCR extracted text and per-page breakdown",
)
async def get_result(document_id: int) -> OcrResultResponse:
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found.")

    if doc["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"OCR not complete. Current status: {doc['status']}",
        )

    result = service.get_result(document_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR result not found.")

    pages = [OcrPageResult(**p) for p in result.get("pages", [])]
    return OcrResultResponse(
        document_id=document_id,
        textract_job_id=result.get("textract_job_id"),
        extracted_text=result.get("extracted_text"),
        page_count=result.get("page_count", 1),
        confidence_avg=result.get("confidence_avg"),
        pages=pages,
        created_at=result.get("created_at"),
    )


@router.get(
    "/health",
    response_model=OcrHealthResponse,
    summary="Check Google Vision connectivity",
)
async def ocr_health() -> OcrHealthResponse:
    health = service.check_ocr_health()
    return OcrHealthResponse(**health)


# ── AI Analysis endpoint ────────────────────────────────────────────────────────

@router.post(
    "/{document_id}/analyze",
    summary="Run LLM analysis on the OCR-extracted text",
    description=(
        "Sends the extracted text from a completed OCR document through the "
        "EREBUS LLM pipeline. Returns a structured analysis including an "
        "executive summary, key entities, sentiment, and action items / flags.\n\n"
        "Requires `status=completed` on the document."
    ),
)
async def analyze_document(
    document_id: int,
) -> dict:
    # 1. Fetch document + verify completed
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
    if doc["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"OCR not complete. Current status: {doc['status']}",
        )

    # 2. Fetch extracted text
    result = service.get_result(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="OCR result not found.")

    extracted_text = (result.get("extracted_text") or "").strip()
    if not extracted_text:
        raise HTTPException(status_code=422, detail="No text extracted — cannot analyse.")

    # 3. Truncate to ~6000 chars to stay within token limits (most docs are shorter)
    MAX_CHARS = 6000
    text_snippet = extracted_text[:MAX_CHARS]
    if len(extracted_text) > MAX_CHARS:
        text_snippet += f"\n\n[... {len(extracted_text) - MAX_CHARS} additional characters truncated ...]"

    file_name = doc.get("file_name", "document")

    # 4. Build prompt
    system_prompt = (
        "You are an expert document analyst for an institutional research platform.\n"
        "You are given raw text extracted via OCR from a financial or business document.\n"
        "Your job is to produce a precise, structured analysis of the document's content.\n"
        "Be concise, factual, and use clear language. Do not make up information."
    )

    user_prompt = f"""Analyse the following OCR-extracted text from '{file_name}' and return a JSON object with exactly these keys:

{{
  "summary": "<3-5 sentence executive summary of the document's main content>",
  "document_type": "<best guess of document type: Annual Report | Earnings Transcript | Financial Statement | Contract | Research Report | Other>",
  "key_entities": {{
    "companies": ["list of company names mentioned"],
    "people": ["list of people/names mentioned"],
    "dates": ["key dates or time periods"],
    "financial_figures": ["key numbers, amounts, percentages"]
  }},
  "sentiment": {{
    "label": "positive | neutral | negative | mixed",
    "score": <float 0.0-1.0 where 1.0 = very positive>,
    "reasoning": "<1-2 sentence explanation>"
  }},
  "key_topics": ["list of 3-6 main topics covered"],
  "action_items": ["list of notable items requiring attention, red flags, or follow-ups — empty list if none"],
  "confidence": "<high | medium | low — based on OCR text quality>"
}}

Return ONLY valid JSON. No markdown, no explanation.

--- DOCUMENT TEXT START ---
{text_snippet}
--- DOCUMENT TEXT END ---"""

    # 5. Call Groq via OpenAI-compatible API (same pattern as llm_explainer.py — no 'groq' SDK needed)
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not set in the environment. Cannot run AI analysis.",
        )

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=1500,
            temperature=0.1,
        )
        raw_text = (resp.choices[0].message.content or "").strip()

        # Strip ```json ... ``` fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        analysis = json.loads(raw_text)

    except json.JSONDecodeError as exc:
        logger.warning("Groq returned non-JSON for doc_id=%s: %s", document_id, exc)
        analysis = {
            "summary": raw_text[:500] if "raw_text" in dir() else "Analysis could not be parsed.",
            "document_type": "Unknown",
            "key_entities": {"companies": [], "people": [], "dates": [], "financial_figures": []},
            "sentiment": {"label": "neutral", "score": 0.5, "reasoning": "Could not parse sentiment."},
            "key_topics": [],
            "action_items": [],
            "confidence": "low",
            "_parse_error": str(exc),
        }
    except Exception as exc:
        logger.error("LLM analysis failed for doc_id=%s: %s", document_id, exc)
        raise HTTPException(
            status_code=503,
            detail=f"AI analysis failed: {exc}",
        )

    return {
        "document_id": document_id,
        "file_name": file_name,
        "provider": "groq",
        "analysis": analysis,
    }
