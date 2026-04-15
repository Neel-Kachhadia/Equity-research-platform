"""
PostgreSQL database connection and initialization utilities.
AWS RDS PostgreSQL (db.t4g.micro - Free Tier)
"""

import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from core.config import settings

logger = logging.getLogger(__name__)

_connection_pool: Optional[SimpleConnectionPool] = None


def _get_pool() -> SimpleConnectionPool:
    global _connection_pool
    
    if _connection_pool is None:
        conn_args = settings.database.get_connection_args()
        
        _connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=settings.database.pool_size,
            **conn_args
        )
        logger.info(f"PostgreSQL connection pool created (size: {settings.database.pool_size})")
    
    return _connection_pool


@contextmanager
def get_connection():
    pool = _get_pool()
    conn = None
    try:
        conn = pool.getconn()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            pool.putconn(conn)


@contextmanager
def get_cursor(cursor_factory=RealDictCursor):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur
            conn.commit()


def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def execute_single(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def execute_write(query: str, params: tuple = (), returning: str = "id") -> Optional[int]:
    if "RETURNING" not in query.upper():
        query = f"{query.rstrip(';')} RETURNING {returning}"
    
    with get_cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()
        return result[returning] if result else None


def init_db() -> None:
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id          SERIAL PRIMARY KEY,
                company_id  VARCHAR(50) NOT NULL,
                year        VARCHAR(10) NOT NULL,
                doc_type    VARCHAR(50) NOT NULL,
                s3_path     TEXT NOT NULL,
                filename    VARCHAR(255),
                file_size   BIGINT,
                status      VARCHAR(20) NOT NULL DEFAULT 'pending',
                error_message TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id          SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                embedding_id VARCHAR(255),
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_jobs (
                id          SERIAL PRIMARY KEY,
                job_type    VARCHAR(50) NOT NULL,
                status      VARCHAR(20) NOT NULL DEFAULT 'pending',
                total_files INTEGER DEFAULT 0,
                processed   INTEGER DEFAULT 0,
                failed      INTEGER DEFAULT 0,
                started_at  TIMESTAMP,
                completed_at TIMESTAMP,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alpha_scores (
                id          SERIAL PRIMARY KEY,
                company_id  VARCHAR(50) NOT NULL,
                year        VARCHAR(10) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                score_value DECIMAL(10, 4) NOT NULL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_id, year, metric_name)
            )
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_company_year 
            ON documents(company_id, year)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_status 
            ON documents(status)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_alpha_scores_lookup 
            ON alpha_scores(company_id, year, metric_name)
        """)
        
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        cur.execute("DROP TRIGGER IF EXISTS update_documents_updated_at ON documents")
        cur.execute("""
            CREATE TRIGGER update_documents_updated_at
                BEFORE UPDATE ON documents
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)
        
        logger.info("PostgreSQL tables initialised successfully")

        # ── OCR tables ──────────────────────────────────────────────────
        from modules.ocr.models import init_ocr_tables
        init_ocr_tables()


def check_db_health() -> bool:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def close_connections():
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Database connection pool closed")
        #s