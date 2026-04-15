"""
EREBUS · Audio Intelligence — Earnings Call Analysis Engine
============================================================
Processes earnings call transcripts (or audio via Amazon Transcribe) and
generates structured behavioural signals for the Credibility Alpha.

Pipeline:
  audio  → [Transcribe] → transcript
  transcript → speaker_classify → clean → sentiment → hesitation → tone → signal

No ML training required. All analysis is rule-based and deterministic.
Outputs are structured JSON, fully traceable, and feed directly into α₆.
"""

from __future__ import annotations

import io
import json
import logging
import re
import statistics
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 · Lexicons
# ══════════════════════════════════════════════════════════════════════════════

FILLER_WORDS = {
    "uh", "um", "er", "ah", "hmm", "uhh", "umm", "erm",
    "you know", "i mean", "like", "basically", "literally",
    "right", "okay", "so", "well",
}

HEDGE_PHRASES = {
    "we believe", "we think", "we expect", "we hope", "we anticipate",
    "might", "may", "could", "should", "would", "possibly", "potentially",
    "approximately", "roughly", "around", "about", "nearly", "almost",
    "subject to", "depending on", "assuming", "if and when",
    "going forward", "in the coming", "we remain", "we are cautiously",
    "challenges ahead", "headwinds", "uncertain", "uncertainty",
    "difficult", "challenging", "volatile", "fluctuating",
}

POSITIVE_WORDS = {
    "strong", "robust", "excellent", "outstanding", "record", "growth",
    "increased", "improved", "beat", "exceeded", "delivering", "confident",
    "momentum", "accelerating", "expanding", "opportunity", "optimistic",
    "solid", "resilient", "ahead", "outperform", "positive", "success",
    "gain", "winning", "leadership", "milestone", "breakthrough",
}

NEGATIVE_WORDS = {
    "decline", "dropped", "fell", "miss", "shortfall", "disappointing",
    "weak", "slowdown", "headwind", "pressure", "loss", "concern",
    "challenging", "difficult", "uncertain", "reduced", "lower",
    "contraction", "erosion", "deterioration", "risk", "vulnerable",
    "struggle", "difficult", "cautious", "worried",
}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 · Data Structures
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Segment:
    speaker_id:    str        # "speaker_0", "speaker_1", ...
    speaker_type:  str        # "Management" | "Analyst" | "Unknown"
    text:          str        # raw text of this turn
    clean_text:    str = ""   # preprocessed text
    timestamp:     Optional[str] = None
    sentiment:     str = "neutral"      # positive/neutral/negative
    sentiment_confidence: float = 0.5
    hesitation_score: float = 0.0
    hedge_count:   int = 0
    filler_count:  int = 0
    word_count:    int = 0


@dataclass
class AudioCredibilitySignal:
    # Top-level signals
    sentiment:           str   = "neutral"     # dominant management sentiment
    sentiment_score:     float = 0.5           # 0=negative, 1=positive
    hesitation_score:    float = 0.0           # overall filler+hedge / total words
    tone_shift:          bool  = False         # significant sentiment variation
    increasing_hedging:  bool  = False
    # Detailed breakdowns
    management_sentiment: str  = "neutral"
    analyst_sentiment:    str  = "neutral"
    filler_rate:          float = 0.0
    hedge_rate:           float = 0.0
    # Scorecard fields
    tone_label:          str  = "Neutral"      # Positive/Neutral/Negative
    hesitation_label:    str  = "Low"          # Low/Moderate/High
    uncertainty_trend:   str  = "Stable"       # Improving/Stable/Deteriorating
    # Narrative
    interpretation:      str  = ""
    # Feed-through for α₆
    credibility_boost:   float = 0.0    # additive adjustment to α₆ raw_score
    data_quality:        str  = "sufficient"   # sufficient/low/insufficient
    segments_analysed:   int  = 0
    warnings:            List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 · Transcription (Amazon Transcribe)
# ══════════════════════════════════════════════════════════════════════════════

def transcribe_audio(
    audio_file_path: Optional[str] = None,
    s3_uri: Optional[str] = None,
    language_code: str = "en-IN",
    job_name_prefix: str = "erebus_earnings",
) -> Optional[str]:
    """
    Transcribe audio file via Amazon Transcribe with speaker labels.
    Returns the raw transcript text, or None on failure.

    Either audio_file_path (local) or s3_uri must be provided.
    For local files, the file is first uploaded to a temp S3 location.
    """
    import os
    import uuid

    bucket = os.getenv("S3_BUCKET_NAME", "erebus-data-prod")
    region = os.getenv("AWS_REGION", "ap-south-1")

    try:
        import boto3
        transcribe = boto3.client("transcribe", region_name=region)
        s3_client  = boto3.client("s3",         region_name=region)
    except ImportError:
        logger.error("[audio] boto3 not installed — cannot transcribe")
        return None

    # Upload local file to S3 if needed
    if audio_file_path and not s3_uri:
        key = f"audio_uploads/{uuid.uuid4().hex}_{audio_file_path.split('/')[-1]}"
        try:
            s3_client.upload_file(audio_file_path, bucket, key)
            s3_uri = f"s3://{bucket}/{key}"
            logger.info("[audio] Uploaded audio to %s", s3_uri)
        except Exception as e:
            logger.error("[audio] S3 upload failed: %s", e)
            return None

    if not s3_uri:
        logger.error("[audio] No audio source provided")
        return None

    # Start transcription job
    job_name = f"{job_name_prefix}_{int(time.time())}"
    try:
        transcribe.start_transcription_job(
            TranscriptionJobName = job_name,
            Media                = {"MediaFileUri": s3_uri},
            MediaFormat          = s3_uri.rsplit(".", 1)[-1].lower() or "mp3",
            LanguageCode         = language_code,
            Settings             = {
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": 4,
            },
        )
        logger.info("[audio] Transcription job started: %s", job_name)
    except Exception as e:
        logger.error("[audio] Failed to start transcription job: %s", e)
        return None

    # Poll for completion (max 10 minutes)
    for _ in range(120):
        time.sleep(5)
        try:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            state  = status["TranscriptionJob"]["TranscriptionJobStatus"]
            if state == "COMPLETED":
                uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                import urllib.request
                with urllib.request.urlopen(uri) as resp:
                    raw = json.loads(resp.read())
                return _parse_transcribe_output(raw)
            elif state == "FAILED":
                logger.error("[audio] Transcription job failed: %s", status)
                return None
        except Exception as e:
            logger.warning("[audio] Polling error: %s", e)

    logger.error("[audio] Transcription job timed out: %s", job_name)
    return None


def _parse_transcribe_output(raw: Dict) -> str:
    """Extract speaker-labelled text from Amazon Transcribe JSON output."""
    try:
        items    = raw["results"]["items"]
        speakers = raw["results"].get("speaker_labels", {}).get("segments", [])

        # Build a map: item_index → speaker_label
        speaker_map: Dict[int, str] = {}
        for seg in speakers:
            for item in seg.get("items", []):
                speaker_map[item["speaker_label"]] = seg["speaker_label"]

        # Reconstruct transcript with speaker labels
        lines   = []
        current_speaker = None
        current_words   = []

        for item in items:
            if item["type"] == "punctuation":
                if current_words:
                    current_words[-1] += item["alternatives"][0]["content"]
                continue
            word    = item["alternatives"][0]["content"]
            speaker = item.get("speaker_label", "speaker_0")
            if speaker != current_speaker:
                if current_words and current_speaker:
                    lines.append(f"[{current_speaker}] {' '.join(current_words)}")
                current_speaker = speaker
                current_words   = [word]
            else:
                current_words.append(word)

        if current_words and current_speaker:
            lines.append(f"[{current_speaker}] {' '.join(current_words)}")

        return "\n".join(lines)

    except Exception as e:
        logger.error("[audio] Failed to parse Transcribe output: %s", e)
        # Fallback: just return the plain transcript text
        try:
            return raw["results"]["transcripts"][0]["transcript"]
        except Exception:
            return ""


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 · Speaker Classification
# ══════════════════════════════════════════════════════════════════════════════

def classify_speakers(transcript_text: str) -> List[Segment]:
    """
    Parse transcript text into Segments with speaker type classification.

    Supported formats:
      [speaker_0] text...        (Amazon Transcribe output)
      Speaker 1: text...
      Management: text...
      Q: / A: format
      Plain text (no labels → single Management block)
    """
    segments: List[Segment] = []

    # ── Detect format ─────────────────────────────────────────────────────────
    labelled_re = re.compile(
        r"^\s*\[?(speaker[_\s]\d+|speaker\d+|management|analyst|"
        r"ceo|cfo|moderator|operator|q|a|questioner|presenter)\]?\s*[:\-]?\s*",
        re.IGNORECASE,
    )
    lines = [l.strip() for l in transcript_text.split("\n") if l.strip()]

    if not lines:
        return []

    # Heuristic: detect Q&A section boundary
    qa_keywords = re.compile(
        r"\b(question[s]? and answer|q\s*&\s*a|open.*floor|moderator|operator)\b",
        re.IGNORECASE,
    )
    qa_start_idx = None
    for i, line in enumerate(lines):
        if qa_keywords.search(line):
            qa_start_idx = i
            break

    # Parse lines into raw segments
    raw_segments: List[Tuple[str, str]] = []    # (speaker_id, text)
    for i, line in enumerate(lines):
        m = labelled_re.match(line)
        if m:
            speaker_id = m.group(1).lower().replace(" ", "_")
            text       = line[m.end():].strip()
            raw_segments.append((speaker_id, text))
        else:
            # Continuation or unlabelled — attach to previous or create generic
            if raw_segments:
                prev_id, prev_text = raw_segments[-1]
                raw_segments[-1]  = (prev_id, f"{prev_text} {line}")
            else:
                raw_segments.append(("speaker_0", line))

    # Assign speaker types
    unique_speakers = list(dict.fromkeys(s for s, _ in raw_segments))
    speaker_type_map: Dict[str, str] = {}

    for sid in unique_speakers:
        lsid = sid.lower()
        if any(x in lsid for x in ("management", "ceo", "cfo", "coo", "presenter")):
            speaker_type_map[sid] = "Management"
        elif any(x in lsid for x in ("analyst", "questioner", "q")):
            speaker_type_map[sid] = "Analyst"
        elif lsid in ("operator", "moderator", "a"):
            speaker_type_map[sid] = "Management" if lsid == "a" else "Unknown"
        else:
            # Positional heuristic:
            # First 1-2 unique speakers → Management (opening statement)
            # Later speakers in Q&A → Analyst
            idx = unique_speakers.index(sid)
            if idx < 2:
                speaker_type_map[sid] = "Management"
            else:
                speaker_type_map[sid] = "Analyst"

    # Build Segment objects
    for line_idx, (sid, text) in enumerate(raw_segments):
        if not text.strip():
            continue

        # Override type if we're past Q&A boundary
        stype = speaker_type_map.get(sid, "Unknown")
        if qa_start_idx and line_idx > qa_start_idx:
            # In Q&A: alternate between Analyst and Management
            if stype == "Unknown":
                stype = "Analyst" if line_idx % 2 == 0 else "Management"

        segments.append(Segment(
            speaker_id   = sid,
            speaker_type = stype,
            text         = text,
        ))

    return segments


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 · Text Preprocessing
# ══════════════════════════════════════════════════════════════════════════════

def preprocess(text: str) -> str:
    """Clean and normalise text while preserving sentence boundaries."""
    if not text:
        return ""
    text = text.lower()
    # Remove non-alphanumeric except punctuation needed for sentences
    text = re.sub(r"[^\w\s\.\!\?\,\;\:\-\']", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 · Sentiment Analysis (rule-based, no ML dependency)
# ══════════════════════════════════════════════════════════════════════════════

def analyse_sentiment(text: str) -> Tuple[str, float]:
    """
    Lightweight lexicon-based sentiment analysis.
    Returns (label, confidence) where:
      label      ∈ {"positive", "neutral", "negative"}
      confidence ∈ [0, 1]
    """
    if not text:
        return "neutral", 0.5

    words  = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return "neutral", 0.5

    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total     = len(words)

    pos_rate = pos_count / total
    neg_rate = neg_count / total

    delta = pos_rate - neg_rate

    if delta > 0.02:
        label      = "positive"
        confidence = min(0.95, 0.5 + delta * 10)
    elif delta < -0.02:
        label      = "negative"
        confidence = min(0.95, 0.5 + abs(delta) * 10)
    else:
        label      = "neutral"
        confidence = 0.5 + (0.3 - abs(delta) * 10)  # closer to 0 delta → more confident neutral

    return label, max(0.35, min(0.95, round(confidence, 3)))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 · Hesitation Detection
# ══════════════════════════════════════════════════════════════════════════════

def compute_hesitation(text: str) -> Dict[str, Any]:
    """
    Detect fillers and hedges in text.

    Returns:
      filler_count, hedge_count, word_count, hesitation_score,
      filler_rate, hedge_rate
    """
    if not text:
        return {
            "filler_count": 0, "hedge_count": 0,
            "word_count": 0, "hesitation_score": 0.0,
            "filler_rate": 0.0, "hedge_rate": 0.0,
        }

    lowered = text.lower()
    words   = re.findall(r"\b\w+\b", lowered)
    total   = len(words)
    if total == 0:
        return {
            "filler_count": 0, "hedge_count": 0,
            "word_count": 0, "hesitation_score": 0.0,
            "filler_rate": 0.0, "hedge_rate": 0.0,
        }

    # Single-word fillers
    filler_count = sum(1 for w in words if w in FILLER_WORDS)

    # Multi-word hedge phrases (substring match on lowered text)
    hedge_count  = 0
    for phrase in HEDGE_PHRASES:
        hedge_count += len(re.findall(r"\b" + re.escape(phrase) + r"\b", lowered))

    hesitation_score = (filler_count + hedge_count) / total

    return {
        "filler_count":     filler_count,
        "hedge_count":      hedge_count,
        "word_count":       total,
        "hesitation_score": round(hesitation_score, 4),
        "filler_rate":      round(filler_count / total, 4),
        "hedge_rate":       round(hedge_count  / total, 4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 · Tone Consistency
# ══════════════════════════════════════════════════════════════════════════════

def _sentiment_to_score(label: str) -> float:
    return {"positive": 1.0, "neutral": 0.5, "negative": 0.0}.get(label, 0.5)


def analyse_tone_consistency(segments: List[Segment]) -> Dict[str, Any]:
    """
    Detect tone shifts and increasing uncertainty across segments.
    Returns tone_shift (bool) and uncertainty_trend.
    """
    mgmt_segments = [s for s in segments if s.speaker_type == "Management"]

    if len(mgmt_segments) < 2:
        return {
            "tone_shift":         False,
            "increasing_hedging": False,
            "sentiment_variance": 0.0,
            "hesitation_trend":   "stable",
        }

    sent_scores = [_sentiment_to_score(s.sentiment) for s in mgmt_segments]
    hesit_scores = [s.hesitation_score for s in mgmt_segments]

    sentiment_variance = statistics.variance(sent_scores) if len(sent_scores) >= 2 else 0.0

    # Tone shift = high variance in sentiment
    tone_shift = sentiment_variance > 0.04

    # Hedging trend — compare first half vs second half
    mid = len(hesit_scores) // 2
    first_half  = statistics.mean(hesit_scores[:mid]) if hesit_scores[:mid] else 0
    second_half = statistics.mean(hesit_scores[mid:]) if hesit_scores[mid:] else 0
    increasing_hedging = second_half > first_half + 0.02

    if increasing_hedging:
        hesitation_trend = "deteriorating"
    elif second_half < first_half - 0.02:
        hesitation_trend = "improving"
    else:
        hesitation_trend = "stable"

    return {
        "tone_shift":         tone_shift,
        "increasing_hedging": increasing_hedging,
        "sentiment_variance": round(sentiment_variance, 4),
        "hesitation_trend":   hesitation_trend,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 · Main Orchestrator
# ══════════════════════════════════════════════════════════════════════════════

def analyse_transcript(
    transcript_text: Optional[str] = None,
    audio_path:      Optional[str] = None,
    s3_audio_uri:    Optional[str] = None,
) -> AudioCredibilitySignal:
    """
    Full pipeline. Accepts either:
      - transcript_text (str)  → skip Transcribe
      - audio_path or s3_audio_uri → run Amazon Transcribe first
    """
    warnings: List[str] = []

    # ── Transcription ─────────────────────────────────────────────────────────
    if not transcript_text:
        if audio_path or s3_audio_uri:
            logger.info("[audio] Transcribing audio...")
            transcript_text = transcribe_audio(
                audio_file_path = audio_path,
                s3_uri          = s3_audio_uri,
            )
        if not transcript_text:
            return AudioCredibilitySignal(
                data_quality    = "insufficient",
                interpretation  = "Insufficient data for audio analysis.",
                warnings        = ["No transcript or audio provided"],
            )

    # Guard: minimum length
    word_count_total = len(transcript_text.split())
    if word_count_total < 50:
        return AudioCredibilitySignal(
            data_quality   = "low",
            interpretation = "Transcript too short for reliable analysis.",
            warnings       = [f"Only {word_count_total} words — minimum 50 required"],
        )

    # ── Speaker Classification ─────────────────────────────────────────────────
    segments = classify_speakers(transcript_text)
    if not segments:
        return AudioCredibilitySignal(
            data_quality   = "insufficient",
            interpretation = "Insufficient data for audio analysis.",
            warnings       = ["No parseable segments found in transcript"],
        )

    # ── Per-segment analysis ───────────────────────────────────────────────────
    for seg in segments:
        seg.clean_text            = preprocess(seg.text)
        hes                       = compute_hesitation(seg.clean_text)
        seg.hesitation_score      = hes["hesitation_score"]
        seg.filler_count          = hes["filler_count"]
        seg.hedge_count           = hes["hedge_count"]
        seg.word_count            = hes["word_count"]
        seg.sentiment, seg.sentiment_confidence = analyse_sentiment(seg.clean_text)

    mgmt_segs    = [s for s in segments if s.speaker_type == "Management"]
    analyst_segs = [s for s in segments if s.speaker_type == "Analyst"]

    # ── Aggregate sentiment ────────────────────────────────────────────────────
    def dominant_sentiment(segs: List[Segment]) -> Tuple[str, float]:
        if not segs:
            return "neutral", 0.5
        scores = [_sentiment_to_score(s.sentiment) for s in segs]
        mean   = statistics.mean(scores)
        if mean >= 0.6:
            return "positive", min(0.95, mean)
        elif mean <= 0.4:
            return "negative", min(0.95, 1 - mean)
        return "neutral", 0.5

    mgmt_sent_label, mgmt_sent_score       = dominant_sentiment(mgmt_segs)
    analyst_sent_label, _                  = dominant_sentiment(analyst_segs)
    overall_sent_label, overall_sent_score = dominant_sentiment(segments)

    # ── Aggregate hesitation ───────────────────────────────────────────────────
    all_words    = sum(s.word_count    for s in segments) or 1
    all_fillers  = sum(s.filler_count  for s in segments)
    all_hedges   = sum(s.hedge_count   for s in segments)
    mgmt_words   = sum(s.word_count    for s in mgmt_segs) or 1
    mgmt_fillers = sum(s.filler_count  for s in mgmt_segs)
    mgmt_hedges  = sum(s.hedge_count   for s in mgmt_segs)

    overall_hesitation = (all_fillers + all_hedges) / all_words
    mgmt_hesitation    = (mgmt_fillers + mgmt_hedges) / mgmt_words
    filler_rate        = all_fillers / all_words
    hedge_rate         = all_hedges  / all_words

    # ── Tone consistency ───────────────────────────────────────────────────────
    tone_info = analyse_tone_consistency(segments)

    # ── Labels ────────────────────────────────────────────────────────────────
    tone_label = {"positive": "Positive", "neutral": "Neutral", "negative": "Negative"}[mgmt_sent_label]

    if mgmt_hesitation > 0.20:
        hesitation_label = "High"
    elif mgmt_hesitation > 0.10:
        hesitation_label = "Moderate"
    else:
        hesitation_label = "Low"

    uncertainty_trend = {
        "deteriorating": "Deteriorating",
        "improving":     "Improving",
        "stable":        "Stable",
    }.get(tone_info["hesitation_trend"], "Stable")

    # ── Credibility boost for α₆ ──────────────────────────────────────────────
    # Positive signal: strong positive management tone + low hesitation
    # Negative signal: negative tone or high hesitation
    credibility_boost = (
        (mgmt_sent_score - 0.5) * 0.2          # sentiment contribution (−0.1 to +0.1)
        - (mgmt_hesitation * 0.3)               # hesitation penalty
        + (0.05 if not tone_info["tone_shift"] else -0.05)   # consistency bonus/penalty
    )
    credibility_boost = round(max(-0.3, min(0.3, credibility_boost)), 4)

    # ── Natural language interpretation ───────────────────────────────────────
    interpretation = _build_interpretation(
        tone_label, hesitation_label, uncertainty_trend,
        tone_info["tone_shift"], tone_info["increasing_hedging"],
        mgmt_hesitation,
    )

    return AudioCredibilitySignal(
        sentiment            = overall_sent_label,
        sentiment_score      = round(overall_sent_score, 3),
        hesitation_score     = round(overall_hesitation, 4),
        tone_shift           = tone_info["tone_shift"],
        increasing_hedging   = tone_info["increasing_hedging"],
        management_sentiment = mgmt_sent_label,
        analyst_sentiment    = analyst_sent_label,
        filler_rate          = round(filler_rate, 4),
        hedge_rate           = round(hedge_rate, 4),
        tone_label           = tone_label,
        hesitation_label     = hesitation_label,
        uncertainty_trend    = uncertainty_trend,
        interpretation       = interpretation,
        credibility_boost    = credibility_boost,
        data_quality         = "sufficient",
        segments_analysed    = len(segments),
        warnings             = warnings,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 · Integration with α₆ Credibility Alpha
# ══════════════════════════════════════════════════════════════════════════════

def enrich_credibility_alpha(
    alpha_result: Dict[str, Any],
    signal: AudioCredibilitySignal,
) -> Dict[str, Any]:
    """
    Apply the audio credibility boost to an existing α₆ result dict.
    Returns an enriched copy with audio_signals attached.
    """
    if signal.data_quality == "insufficient":
        alpha_result["audio_intelligence"] = {
            "available": False,
            "reason":    signal.interpretation,
        }
        return alpha_result

    # Adjust raw score by credibility boost
    old_score = alpha_result.get("raw_score", 0.0)
    new_score = round(old_score + signal.credibility_boost, 6)

    enriched = dict(alpha_result)
    enriched["raw_score"]             = new_score
    enriched["audio_credibility_boost"] = signal.credibility_boost
    enriched["audio_intelligence"]    = {
        "available":        True,
        # Scorecard-ready block
        "scorecard": {
            "tone":            signal.tone_label,
            "hesitation":      f"{signal.hesitation_label} ({signal.hesitation_score:.2f})",
            "uncertainty_trend": signal.uncertainty_trend,
            "insight":         signal.interpretation,
            "confidence":      "High" if signal.segments_analysed >= 5 else "Medium",
        },
        # Raw signal
        "signal": {
            "sentiment":         signal.sentiment,
            "hesitation_score":  signal.hesitation_score,
            "tone_shift":        signal.tone_shift,
            "increasing_hedging": signal.increasing_hedging,
            "filler_rate":       signal.filler_rate,
            "hedge_rate":        signal.hedge_rate,
            "interpretation":    signal.interpretation,
        },
        "segments_analysed": signal.segments_analysed,
        "data_quality":      signal.data_quality,
        "warnings":          signal.warnings,
    }
    return enriched


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_interpretation(
    tone_label: str,
    hesitation_label: str,
    uncertainty_trend: str,
    tone_shift: bool,
    increasing_hedging: bool,
    mgmt_hesitation: float,
) -> str:
    """Build a plain-English sentence for the LLM / scorecard."""
    parts = [f"Management tone is {tone_label.lower()}."]

    if hesitation_label == "High":
        parts.append(
            f"Hesitation is high ({mgmt_hesitation:.0%} of words are fillers or hedges), "
            "suggesting significant uncertainty in forward guidance."
        )
    elif hesitation_label == "Moderate":
        parts.append(
            f"Hesitation is moderate ({mgmt_hesitation:.0%}), consistent with normal cautious language."
        )
    else:
        parts.append("Language is direct and confident with low hesitation.")

    if tone_shift:
        parts.append("Notable tone shifts were detected across the call.")
    if increasing_hedging:
        parts.append("Hedging language increased through the call, indicating growing uncertainty.")
    if uncertainty_trend == "Improving":
        parts.append("Overall uncertainty trend is improving compared to recent periods.")
    elif uncertainty_trend == "Deteriorating":
        parts.append("Uncertainty trend is deteriorating — management may face increasing challenges.")

    return " ".join(parts)
