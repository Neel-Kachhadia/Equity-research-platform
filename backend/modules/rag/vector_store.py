"""
EREBUS · Vector Store (PostgreSQL + pgvector)
==============================================
AWS Aurora PostgreSQL with pgvector extension.
Stores embeddings and metadata in RDS.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from core.database import get_cursor, execute_query, execute_write, execute_single

logger = logging.getLogger(__name__)


class VectorStore:
    """
    PostgreSQL + pgvector implementation.
    Uses Aurora RDS for persistent vector storage.
    """
    
    def __init__(self, table_name: str = "document_chunks"):
        self.table_name = table_name
        # Extension must be created BEFORE the table (schema uses the vector type)
        self._ensure_pgvector_extension()
        self._ensure_table_exists()
    
    def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is installed."""
        try:
            with get_cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("[VectorStore] pgvector extension ready")
        except Exception as e:
            logger.error("[VectorStore] Failed to create pgvector extension: %s", e)
            raise
    
    def _ensure_table_exists(self):
        """Create table if it doesn't exist."""
        try:
            with get_cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id              SERIAL PRIMARY KEY,
                        chunk_id        VARCHAR(64) UNIQUE NOT NULL,
                        company_id      VARCHAR(50) NOT NULL,
                        document_id     VARCHAR(64),
                        chunk_index     INTEGER,
                        text            TEXT NOT NULL,
                        embedding       vector(384),   -- HuggingFace all-MiniLM-L6-v2 dimension
                        metadata        JSONB,
                        section         VARCHAR(100),
                        chunk_type      VARCHAR(20) DEFAULT 'text',
                        token_count     INTEGER,
                        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_company_id 
                    ON {self.table_name}(company_id)
                """)
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_chunk_id 
                    ON {self.table_name}(chunk_id)
                """)
                
                # IVFFlat index — lists=10 works on empty tables.
                # For production with >10k rows, raise lists to 100.
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding_ivfflat 
                    ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 10)
                """)
                
            logger.info("[VectorStore] Table %s ready", self.table_name)
            
        except Exception as e:
            logger.error("[VectorStore] Failed to create table: %s", e)
            raise
    
    def add_embeddings(
        self,
        embedded_chunks: List[Any],
        company_id: Optional[str] = None,
    ) -> int:
        """
        Add embedded chunks to PostgreSQL.
        
        Args:
            embedded_chunks: List of EmbeddedChunk objects
            company_id: Company identifier
            
        Returns:
            Number of chunks added
        """
        if not embedded_chunks:
            return 0
        
        added = 0
        
        for chunk in embedded_chunks:
            try:
                metadata = dict(chunk.metadata)
                if company_id:
                    metadata["company_id"] = company_id
                
                upsert_sql = f"""
                    INSERT INTO {self.table_name}
                        (chunk_id, company_id, document_id, chunk_index,
                         text, embedding, metadata, section, chunk_type, token_count)
                    VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        text      = EXCLUDED.text,
                        embedding = EXCLUDED.embedding,
                        metadata  = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """
                # Use get_cursor directly — execute_write appends RETURNING
                # which is invalid when returning=None
                with get_cursor() as cur:
                    cur.execute(upsert_sql, (
                        chunk.chunk_id,
                        company_id or metadata.get("company_id", "unknown"),
                        metadata.get("document_id"),
                        chunk.metadata.get("chunk_index"),
                        chunk.text,
                        f"[{','.join(map(str, chunk.embedding))}]",
                        json.dumps(metadata),
                        str(metadata.get("section", ""))[:100],
                        metadata.get("chunk_type", "text"),
                        metadata.get("token_count", 0),
                    ))
                
                added += 1
                
            except Exception as e:
                logger.error("[VectorStore] Failed to add chunk %s: %s", chunk.chunk_id, e)
        
        logger.info("[VectorStore] Added %d chunks to %s", added, self.table_name)
        return added
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        company_id: Optional[str] = None,
        min_similarity: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            company_id: Optional company filter
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of results with text, metadata, and similarity
        """
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        where_clause  = ""
        where_params: list = []
        if company_id:
            where_clause = "AND company_id = %s"
            where_params  = [company_id]
        
        query = f"""
            SELECT 
                chunk_id,
                text,
                metadata,
                section,
                chunk_type,
                company_id,
                1 - (embedding <=> %s::vector) AS similarity
            FROM {self.table_name}
            WHERE 1=1 {where_clause}
                AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        # Params must match SQL placeholders in order:
        # 1. SELECT similarity  -> embedding_str
        # 2. WHERE company_id   -> company_id (0 or 1 item)
        # 3. WHERE min_sim      -> embedding_str, min_similarity
        # 4. ORDER BY           -> embedding_str
        # 5. LIMIT              -> top_k
        params = (
            [embedding_str]
            + where_params
            + [embedding_str, min_similarity, embedding_str, top_k]
        )
        
        try:
            results = execute_query(query, tuple(params))
            
            formatted = []
            for row in results:
                formatted.append({
                    "chunk_id": row["chunk_id"],
                    "text": row["text"],
                    "metadata": row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"] or "{}"),
                    "section": row["section"],
                    "chunk_type": row["chunk_type"],
                    "company_id": row["company_id"],
                    "similarity": float(row["similarity"]),
                })
            
            return formatted
            
        except Exception as e:
            logger.error("[VectorStore] Search failed: %s", e)
            return []
    
    def delete_company(self, company_id: str) -> bool:
        """Delete all chunks for a company."""
        try:
            with get_cursor() as cur:
                cur.execute(f"DELETE FROM {self.table_name} WHERE company_id = %s", (company_id,))
            logger.info("[VectorStore] Deleted chunks for %s", company_id)
            return True
        except Exception as e:
            logger.error("[VectorStore] Failed to delete %s: %s", company_id, e)
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        try:
            with get_cursor() as cur:
                cur.execute(f"DELETE FROM {self.table_name} WHERE document_id = %s", (document_id,))
            logger.info("[VectorStore] Deleted chunks for document %s", document_id)
            return True
        except Exception as e:
            logger.error("[VectorStore] Failed to delete document %s: %s", document_id, e)
            return False
    
    def count(self, company_id: Optional[str] = None) -> int:
        """Count chunks in store."""
        try:
            if company_id:
                query = f"SELECT COUNT(*) as cnt FROM {self.table_name} WHERE company_id = %s"
                result = execute_single(query, (company_id,))
            else:
                query = f"SELECT COUNT(*) as cnt FROM {self.table_name}"
                result = execute_single(query)
            
            return result["cnt"] if result else 0
        except Exception as e:
            logger.error("[VectorStore] Count failed: %s", e)
            return 0
    
    def get_companies(self) -> List[str]:
        """Get list of companies with indexed documents."""
        try:
            query = f"SELECT DISTINCT company_id FROM {self.table_name} ORDER BY company_id"
            results = execute_query(query)
            return [r["company_id"] for r in results]
        except Exception as e:
            logger.error("[VectorStore] Get companies failed: %s", e)
            return []


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store