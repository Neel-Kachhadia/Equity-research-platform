#!/usr/bin/env python3
"""
index_s3_docs.py
================
Pull every PDF/JSON from S3, extract text, and index into the RAG
vector store (Aurora pgvector) so EREBUS can answer from real data.

Run from backend/:
    python index_s3_docs.py [--company TCS] [--limit 5]
"""

import argparse
import io
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import boto3

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BUCKET = os.getenv("S3_BUCKET_NAME", "erebus-data-prod")
REGION = os.getenv("AWS_REGION", "ap-south-1")
PDF_EXTS = {".pdf"}
MIN_CHARS = 200       # skip near-empty extractions
MAX_CHARS_PER_DOC = 200_000   # truncate huge docs so embedding stays fast


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(data: bytes, key: str) -> str:
    """
    Layout-aware PDF extraction using PyMuPDF block structure.
    - Detects bold/large-font lines as section headings (prefixed with ##)
    - Preserves numeric table rows as tab-aligned structured text
    - Tags every block with its page number for chunk provenance
    - Fallback to pdfminer if fitz unavailable
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log.warning("PyMuPDF not installed — falling back to pdfminer")
        return _extract_with_pdfminer(data)

    try:
        doc = fitz.open(stream=data, filetype="pdf")
        sections: list[str] = []
        total_chars = 0

        for page_num, page in enumerate(doc, start=1):
            if total_chars >= MAX_CHARS_PER_DOC:
                break

            page_header = f"\n[Page {page_num}]\n"
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            page_lines: list[str] = [page_header]

            for block in blocks:
                if block.get("type") != 0:   # 0=text, 1=image → skip images
                    continue

                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    # Reconstruct line text
                    line_text = " ".join(s.get("text", "").strip() for s in spans).strip()
                    if not line_text:
                        continue

                    # Detect headings: any span with bold flag or size ≥ 13
                    is_heading = any(
                        (s.get("flags", 0) & 16)           # bold bitmask
                        or s.get("size", 0) >= 13.0
                        for s in spans
                    )

                    # Detect table row: line mostly numbers / currency symbols
                    num_chars = sum(1 for c in line_text if c.isdigit() or c in ",.₹$%()-")
                    is_table_row = len(line_text) > 5 and num_chars / len(line_text) > 0.45

                    if is_heading:
                        page_lines.append(f"\n## {line_text}\n")
                    elif is_table_row:
                        # Tab-align columns for the chunker's numeric table detector
                        cols = [c.strip() for c in re.split(r"\s{2,}", line_text)]
                        page_lines.append("\t".join(cols))
                    else:
                        page_lines.append(line_text)

            page_text = "\n".join(page_lines)
            sections.append(page_text)
            total_chars += len(page_text)

        doc.close()
        full_text = "\n".join(sections).strip()
        return full_text[:MAX_CHARS_PER_DOC]

    except Exception as e:
        log.warning("[%s] PyMuPDF layout parse failed (%s) — falling back", key, e)
        try:
            import fitz
            doc = fitz.open(stream=data, filetype="pdf")
            text = "\n".join(p.get_text() for p in doc).strip()
            doc.close()
            return text[:MAX_CHARS_PER_DOC]
        except Exception:
            return _extract_with_pdfminer(data)


def _extract_with_pdfminer(data: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        out = io.StringIO()
        extract_text_to_fp(io.BytesIO(data), out, laparams=LAParams(
            line_margin=0.3,
            word_margin=0.1,
            char_margin=2.0,
        ))
        return out.getvalue()[:MAX_CHARS_PER_DOC]
    except Exception as e:
        log.warning("pdfminer also failed: %s", e)
        return ""


def extract_text_from_json(data: bytes, key: str) -> str:
    """Convert Yahoo Finance JSON to a readable text blob for embedding."""
    try:
        obj = json.loads(data.decode("utf-8", errors="replace"))
        parts = []
        company = key.split("/")[0]
        parts.append(f"Company: {company}")
        if "info" in obj:
            info = obj["info"]
            for k, v in info.items():
                if v is not None:
                    parts.append(f"{k}: {v}")
        if "financials" in obj and obj["financials"]:
            parts.append("\n--- Financial Data ---")
            fin = obj["financials"]
            for section, rows in fin.items():
                parts.append(f"\n[{section}]")
                if isinstance(rows, list):
                    for row in rows[:20]:
                        parts.append(str(row))
                elif isinstance(rows, dict):
                    for k, v in list(rows.items())[:20]:
                        parts.append(f"  {k}: {v}")
        return "\n".join(parts)[:MAX_CHARS_PER_DOC]
    except Exception as e:
        log.warning("[%s] JSON parse error: %s", key, e)
        return ""


# ── S3 helpers ────────────────────────────────────────────────────────────────
def list_s3_objects(s3, company_filter: str = None) -> List[Dict]:
    """List all indexable objects in the bucket."""
    paginator = s3.get_paginator("list_objects_v2")
    prefix = f"{company_filter}/" if company_filter else ""
    objects = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            ext = Path(key).suffix.lower()
            # Only PDF and Yahoo JSON files
            if ext == ".pdf" or key.endswith("yahoo_data.json") or "yahoo_data" in key:
                objects.append({"key": key, "size": obj["Size"], "ext": ext})
    return objects


def download_object(s3, key: str) -> bytes:
    resp = s3.get_object(Bucket=BUCKET, Key=key)
    return resp["Body"].read()


# ── Main indexing logic ────────────────────────────────────────────────────────
def build_document(key: str, data: bytes) -> Dict[str, Any]:
    """Convert S3 object into a {text, metadata} dict for the RAG pipeline."""
    parts = key.split("/")
    company_id = parts[0] if parts else "UNKNOWN"
    category = parts[1] if len(parts) > 1 else "General"
    filename = parts[-1]
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(data, key)
    elif ext == ".json":
        text = extract_text_from_json(data, key)
    else:
        text = data.decode("utf-8", errors="replace")[:MAX_CHARS_PER_DOC]

    return {
        "text": text,
        "metadata": {
            "company_id": company_id,
            "category": category,
            "filename": filename,
            "s3_key": key,
            "source": "s3",
        },
    }


def run_indexing(company_filter: str = None, limit: int = None, dry_run: bool = False):
    log.info("=" * 60)
    log.info("  EREBUS S3 → RAG Indexer")
    log.info("  Bucket : %s", BUCKET)
    log.info("  Filter : %s", company_filter or "all companies")
    log.info("=" * 60)

    s3 = boto3.client("s3", region_name=REGION)

    log.info("Listing S3 objects...")
    objects = list_s3_objects(s3, company_filter)
    log.info("Found %d indexable objects", len(objects))

    if limit:
        objects = objects[:limit]
        log.info("Limiting to first %d objects", limit)

    if not objects:
        log.warning("No objects found — nothing to index!")
        return

    if not dry_run:
        # Import RAG pipeline (needs Django/FastAPI app context + DB)
        try:
            from modules.rag.pipeline import RagPipeline
            embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
            rag = RagPipeline(
                chunk_size=800,       # ~600 tokens — captures full financial paragraphs
                chunk_overlap=120,    # 15% overlap — preserves cross-chunk context
                embedding_provider=embedding_provider,
            )
            log.info("RAG pipeline initialized (provider=%s, chunk=800w, overlap=120w)", embedding_provider)
        except Exception as e:
            log.error("Failed to initialize RAG pipeline: %s", e)
            log.error("Ensure DATABASE_URL and embedding API key are set in .env")
            sys.exit(1)

    # Group by company for batch indexing
    by_company: Dict[str, List] = {}
    for obj in objects:
        co = obj["key"].split("/")[0]
        by_company.setdefault(co, []).append(obj)

    total_indexed = 0
    total_skipped = 0
    total_failed = 0

    for company_id, company_objects in sorted(by_company.items()):
        log.info("\n── %s  (%d objects) ────────────────────", company_id, len(company_objects))
        docs = []

        for obj in company_objects:
            key = obj["key"]
            size_kb = obj["size"] // 1024
            try:
                log.info("  Download: %s  (%d KB)", key, size_kb)
                data = download_object(s3, key)
                doc = build_document(key, data)
                text = doc["text"]

                if len(text) < MIN_CHARS:
                    log.warning("  [SKIP] Too short (%d chars): %s", len(text), key)
                    total_skipped += 1
                    continue

                log.info("  [TEXT]  %d chars extracted from %s", len(text), Path(key).name)
                docs.append(doc)

            except Exception as e:
                log.error("  [FAIL] %s: %s", key, e)
                total_failed += 1

        if not docs:
            log.warning("  No valid documents for %s", company_id)
            continue

        if dry_run:
            log.info("  [DRY] Would index %d docs for %s", len(docs), company_id)
            total_indexed += len(docs)
            continue

        # Index into vector store
        try:
            result = rag.index_documents(company_id=company_id, documents=docs)
            chunks = result.get("chunks_indexed", 0)
            log.info("  ✅ Indexed %d docs → %d chunks for %s", len(docs), chunks, company_id)
            total_indexed += len(docs)
        except Exception as e:
            log.error("  ❌ Indexing failed for %s: %s", company_id, e)
            total_failed += len(docs)

    log.info("\n" + "=" * 60)
    log.info("  DONE")
    log.info("  Indexed : %d documents", total_indexed)
    log.info("  Skipped : %d (too short / empty)", total_skipped)
    log.info("  Failed  : %d", total_failed)
    log.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index S3 PDFs into EREBUS RAG")
    parser.add_argument("--company", help="Only index one company, e.g. TCS")
    parser.add_argument("--limit", type=int, help="Max objects to process")
    parser.add_argument("--dry-run", action="store_true", help="List files without indexing")
    args = parser.parse_args()

    run_indexing(
        company_filter=args.company,
        limit=args.limit,
        dry_run=args.dry_run,
    )
