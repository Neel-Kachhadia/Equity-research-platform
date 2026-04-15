"""
modules/ocr/models.py

PostgreSQL table definitions for the OCR pipeline.
Call init_ocr_tables() from core/database.py :: init_db() at startup.

Tables
------
  ocr_documents   — one row per uploaded file, tracks status lifecycle
  ocr_results     — one row per successful OCR run, stores extracted text + raw JSON
  ocr_result_pages — optional per-page breakdown (populated for multi-page PDFs)
"""

import logging
from core.database import get_cursor

logger = logging.getLogger(__name__)


def init_ocr_tables() -> None:
    """Create OCR tables if they don't already exist."""
    with get_cursor() as cur:

        # ── ocr_documents ─────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ocr_documents (
                id                      SERIAL PRIMARY KEY,
                file_name               VARCHAR(255) NOT NULL,
                s3_bucket               VARCHAR(255) NOT NULL,
                s3_key                  TEXT NOT NULL,
                s3_url                  TEXT,
                mime_type               VARCHAR(100),
                file_size               BIGINT,
                status                  VARCHAR(20) NOT NULL DEFAULT 'uploaded'
                                        CHECK (status IN ('uploaded','processing','completed','failed')),
                upload_created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_started_at   TIMESTAMP,
                processing_completed_at TIMESTAMP,
                error_message           TEXT,
                created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── ocr_results ───────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ocr_results (
                id                  SERIAL PRIMARY KEY,
                document_id         INTEGER NOT NULL
                                    REFERENCES ocr_documents(id) ON DELETE CASCADE,
                textract_job_id     VARCHAR(255),
                extracted_text      TEXT,
                raw_response_json   JSONB,
                page_count          INTEGER DEFAULT 1,
                confidence_avg      NUMERIC(5, 2),
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── ocr_result_pages ──────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ocr_result_pages (
                id          SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL
                            REFERENCES ocr_documents(id) ON DELETE CASCADE,
                page_number INTEGER NOT NULL,
                page_text   TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Indexes ───────────────────────────────────────────────────────────
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_ocr_documents_status
            ON ocr_documents(status)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_ocr_documents_created
            ON ocr_documents(created_at DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_ocr_results_document
            ON ocr_results(document_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_ocr_pages_document
            ON ocr_result_pages(document_id, page_number)
        """)

        # ── updated_at trigger for ocr_documents ──────────────────────────────
        # update_updated_at_column() already exists from init_db(); just add trigger
        cur.execute("DROP TRIGGER IF EXISTS update_ocr_documents_updated_at ON ocr_documents")
        cur.execute("""
            CREATE TRIGGER update_ocr_documents_updated_at
                BEFORE UPDATE ON ocr_documents
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)

        cur.execute("DROP TRIGGER IF EXISTS update_ocr_results_updated_at ON ocr_results")
        cur.execute("""
            CREATE TRIGGER update_ocr_results_updated_at
                BEFORE UPDATE ON ocr_results
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)

        logger.info("OCR tables initialised successfully")
