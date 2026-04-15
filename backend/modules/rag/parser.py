"""
EREBUS · RAG · Document Parser
================================
Parses PDFs into structured per-page text blobs with metadata.
Includes a text cleaning layer to handle messy PDF extraction artefacts.

Pipeline position: S3 download → parse → clean → chunk → embed → store
"""

from __future__ import annotations
import re
import unicodedata
from typing import List, Dict, Any, Optional
from pathlib import Path


def clean_text(raw: str) -> str:
    """
    Normalize whitespace and strip junk characters from PDF-extracted text.
    PDF parsers often produce broken sentences, double spaces, ligature chars, etc.
    """
    if not raw:
        return ""

    # Normalize unicode (handles ligatures like ﬁ → fi)
    text = unicodedata.normalize("NFKC", raw)

    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r"[^\S\n\t]+", " ", text)        # collapse whitespace runs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)  # strip control chars

    # Fix broken hyphenated words across line breaks (common in PDFs)
    text = re.sub(r"-\n(\w)", r"\1", text)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_pdf(
    pdf_path: str,
    company_id: str,
    year: str,
    doc_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Parse a PDF file into a list of per-page dicts ready for chunking.

    Parameters
    ----------
    pdf_path : str
        Absolute path to the PDF file on disk.
    company_id : str
        Company ticker / identifier (e.g. "INFY").
    year : str
        Fiscal year string (e.g. "FY24").
    doc_id : str, optional
        Override document ID. If None, derived as "{company_id}-{year}-AR".

    Returns
    -------
    List of page dicts:
        {
            "doc_id": str,
            "company_id": str,
            "year": str,
            "page": int,
            "text": str       # cleaned text for this page
        }
    """
    from pypdf import PdfReader

    if doc_id is None:
        doc_id = f"{company_id}-{year}-AR"

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(path))
    pages = []

    for page_num, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        cleaned = clean_text(raw)

        if not cleaned:
            continue  # skip blank/image-only pages

        pages.append({
            "doc_id": doc_id,
            "company_id": company_id,
            "year": year,
            "page": page_num,
            "text": cleaned,
        })

    return pages
