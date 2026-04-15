"""
EREBUS · Audio Intelligence — FastAPI Router
=============================================
POST /audio/analyse   → analyse a transcript text
POST /audio/transcribe → upload audio → Groq Whisper → analyse
GET  /audio/healthz    → module health
"""

from __future__ import annotations

import io
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from modules.audio.intelligence import (
    analyse_transcript,
    enrich_credibility_alpha,
    AudioCredibilitySignal,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["Audio Intelligence"])


# ── Groq Whisper transcription ────────────────────────────────────────────────

_MIME_MAP = {
    "mp3":  "audio/mpeg",
    "wav":  "audio/wav",
    "m4a":  "audio/mp4",
    "ogg":  "audio/ogg",
    "webm": "audio/webm",
    "flac": "audio/flac",
    "mp4":  "audio/mp4",
}


async def _transcribe_with_groq(audio_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio bytes via Groq Whisper API.
    Returns the plain-text transcript.

    NOTE: We do NOT use response_format='text' because the Groq SDK v0.x
    returns a typed object in that mode — str(resp) gives the object repr,
    not the transcript. Using default (JSON) mode and accessing .text is
    the correct pattern.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY not configured — cannot transcribe audio")

    ext      = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp3"
    mimetype = _MIME_MAP.get(ext, "audio/mpeg")

    # Prefer the Groq SDK (already a dependency for chat)
    try:
        from groq import Groq  # type: ignore
        client = Groq(api_key=api_key)
        # Use default JSON response format → resp.text contains the transcript
        resp = client.audio.transcriptions.create(
            file  = (filename, io.BytesIO(audio_bytes), mimetype),
            model = "whisper-large-v3-turbo",
            # response_format intentionally omitted → JSON (default)
            # language omitted → Whisper auto-detects (more robust for mixed English)
        )
        text = (getattr(resp, "text", None) or "").strip()
        logger.info("[audio] Groq SDK transcription: %d chars, preview: %.80r", len(text), text[:80])
        return text
    except ImportError:
        logger.debug("[audio] groq SDK not installed — falling back to httpx")
    except Exception as sdk_exc:
        logger.warning("[audio] Groq SDK failed (%s), trying httpx fallback", sdk_exc)

    # Fallback: raw HTTP with httpx (comes with FastAPI / starlette)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as http:
            r = await http.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (filename, audio_bytes, mimetype)},
                data={"model": "whisper-large-v3-turbo"},  # default JSON
            )
            r.raise_for_status()
            payload = r.json()
            text = (payload.get("text") or "").strip()
            logger.info("[audio] httpx transcription: %d chars, preview: %.80r", len(text), text[:80])
            return text
    except Exception as exc:
        logger.error("[audio] Groq Whisper transcription failed: %s", exc)
        raise HTTPException(500, f"Transcription failed: {exc}") from exc


# ── Request / Response models ─────────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    transcript:   str              = Field(..., description="Raw earnings call transcript text")
    company_id:   Optional[str]    = None
    quarter:      Optional[str]    = None         # e.g. "Q3FY25"
    # Optional: existing α₆ result to enrich
    alpha_result: Optional[dict]   = None


class AudioSignalResponse(BaseModel):
    company_id:         Optional[str]
    quarter:            Optional[str]
    sentiment:          str
    sentiment_score:    float
    hesitation_score:   float
    tone_shift:         bool
    increasing_hedging: bool
    management_sentiment: str
    analyst_sentiment:  str
    filler_rate:        float
    hedge_rate:         float
    tone_label:         str
    hesitation_label:   str
    uncertainty_trend:  str
    interpretation:     str
    credibility_boost:  float
    data_quality:       str
    segments_analysed:  int
    warnings:           List[str]
    # Enriched alpha (if alpha_result was provided)
    enriched_alpha:     Optional[dict] = None
    # Transcript text returned after audio upload/transcription
    transcript_text:    Optional[str]  = None

    class Config:
        from_attributes = True


class ScorecardBlock(BaseModel):
    """Flat scorecard block for the frontend."""
    tone:             str
    hesitation:       str
    uncertainty_trend: str
    insight:          str
    confidence:       str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/healthz", summary="Audio module health check")
def audio_health():
    return {"status": "ok", "module": "audio_intelligence"}


@router.post(
    "/analyse",
    response_model=AudioSignalResponse,
    summary="Analyse earnings call transcript",
)
def analyse(req: TranscriptRequest):
    """
    Analyse a transcript and return structured behavioural signals.

    Optionally accepts an existing α₆ credibility_alpha result to enrich
    with the audio signals (boosts/penalises the raw_score).
    """
    if not req.transcript or len(req.transcript.strip()) < 20:
        raise HTTPException(400, "Transcript too short or empty")

    signal: AudioCredibilitySignal = analyse_transcript(
        transcript_text = req.transcript,
    )

    enriched = None
    if req.alpha_result:
        enriched = enrich_credibility_alpha(req.alpha_result, signal)

    logger.info(
        "[audio] Analysed %d segments | tone=%s hesitation=%s quality=%s",
        signal.segments_analysed,
        signal.tone_label,
        signal.hesitation_label,
        signal.data_quality,
    )

    return AudioSignalResponse(
        company_id         = req.company_id,
        quarter            = req.quarter,
        **signal.to_dict(),
        enriched_alpha     = enriched,
    )


@router.post(
    "/transcribe",
    response_model=AudioSignalResponse,
    summary="Upload audio → Groq Whisper → analyse transcript",
)
async def transcribe_and_analyse(
    file:       UploadFile = File(..., description="Audio file (mp3/wav/m4a/ogg/webm)"),
    company_id: Optional[str] = Form(None),
    quarter:    Optional[str] = Form(None),
):
    """
    Upload an audio file → Groq Whisper (instant) → behavioural analysis.

    Returns the full AudioSignalResponse **plus** the raw transcript_text
    so the frontend can display (and optionally edit) what was heard.
    """
    audio_bytes  = await file.read()
    filename     = file.filename or "upload.mp3"

    if not audio_bytes:
        raise HTTPException(400, "Empty audio file")

    logger.info("[audio] Transcribing %s (%d bytes) via Groq Whisper",
                filename, len(audio_bytes))

    # ── 1. Transcribe ────────────────────────────────────────────────────────
    transcript_text = await _transcribe_with_groq(audio_bytes, filename)

    if not transcript_text or len(transcript_text.split()) < 1:
        raise HTTPException(422, "Transcription returned no usable text. "
                                 "Check that the audio file contains audible speech in English.")

    logger.info("[audio] Transcript: %d words", len(transcript_text.split()))

    # ── 2. Analyse transcript ────────────────────────────────────────────────
    signal: AudioCredibilitySignal = analyse_transcript(
        transcript_text=transcript_text,
    )

    return AudioSignalResponse(
        company_id      = company_id,
        quarter         = quarter,
        transcript_text = transcript_text,
        **signal.to_dict(),
        enriched_alpha  = None,
    )


@router.post(
    "/scorecard",
    response_model=ScorecardBlock,
    summary="Get scorecard-ready management credibility block",
)
def scorecard(req: TranscriptRequest):
    """
    Returns only the Management Credibility scorecard block —
    used directly by the frontend scorecard renderer.
    """
    signal = analyse_transcript(transcript_text=req.transcript)

    confidence = "High" if signal.segments_analysed >= 5 else (
        "Medium" if signal.segments_analysed >= 2 else "Low"
    )

    return ScorecardBlock(
        tone             = signal.tone_label,
        hesitation       = f"{signal.hesitation_label} ({signal.hesitation_score:.2f})",
        uncertainty_trend = signal.uncertainty_trend,
        insight          = signal.interpretation,
        confidence       = confidence,
    )
