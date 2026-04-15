"""
EREBUS · RAG Pipeline (AWS Stack)
==================================
End-to-end pipeline: chunk → embed → store (RDS) → cache (Redis).
"""

import logging
from typing import List, Dict, Any, Optional

from .chunking import SemanticChunker, TextChunk
from .embedding import EmbeddingGenerator, EmbeddingProvider
from .vector_store import get_vector_store
from .query import RagRetriever
from .cache import EmbeddingCache

logger = logging.getLogger(__name__)


class RagPipeline:
    """
    Complete RAG pipeline using AWS Aurora RDS + ElastiCache Redis.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        embedding_provider: str = "huggingface",
        embedding_model: Optional[str] = None,
        use_cache: bool = True,
    ):
        self.chunker = SemanticChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.embedding_generator = EmbeddingGenerator(
            provider=EmbeddingProvider(embedding_provider),
            model=embedding_model,
        )
        self.vector_store = get_vector_store()
        self.cache = EmbeddingCache() if use_cache else None
        self.retriever = RagRetriever(
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            use_cache=use_cache,
        )
    
    def index_documents(
        self,
        company_id: str,
        documents: List[Dict[str, Any]],
        clear_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Index documents for a company.
        
        Args:
            company_id: Company identifier
            documents: List of {"text": str, "metadata": dict}
            clear_existing: Whether to delete existing chunks first
            
        Returns:
            Indexing statistics
        """
        if clear_existing:
            self.vector_store.delete_company(company_id)
            if self.cache:
                self.cache.invalidate_company(company_id)
            logger.info("[Pipeline] Cleared existing chunks for %s", company_id)
        
        all_chunks = []
        
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            metadata["company_id"] = company_id
            
            if not text:
                continue
            
            chunks = self.chunker.chunk_document(text, metadata)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.warning("[Pipeline] No chunks generated for %s", company_id)
            return {"company_id": company_id, "chunks_indexed": 0}
        
        # Generate embeddings
        embedded_chunks = self.embedding_generator.embed_chunks(all_chunks)
        
        # Store in PostgreSQL
        self.vector_store.add_embeddings(embedded_chunks, company_id)
        
        # Invalidate cache for this company
        if self.cache:
            self.cache.invalidate_company(company_id)
        
        logger.info("[Pipeline] Indexed %d chunks for %s", len(embedded_chunks), company_id)
        
        return {
            "company_id": company_id,
            "documents_processed": len(documents),
            "chunks_indexed": len(embedded_chunks),
            "storage": "Aurora PostgreSQL (pgvector)",
            "cache": "ElastiCache Redis" if self.cache else "disabled",
        }
    
    def retrieve(
        self,
        query: str,
        company_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query."""
        return self.retriever.retrieve(query, top_k, company_id)
    
    def retrieve_context(
        self,
        query: str,
        company_id: Optional[str] = None,
        top_k: int = 5,
    ) -> str:
        """Retrieve formatted context for LLM."""
        return self.retriever.retrieve_context(query, top_k, company_id, combine=True)
    
    def get_stats(self, company_id: Optional[str] = None) -> Dict[str, Any]:
        """Get indexing statistics."""
        return {
            "total_chunks": self.vector_store.count(),
            "company_chunks": self.vector_store.count(company_id) if company_id else None,
            "indexed_companies": self.vector_store.get_companies(),
            "storage": "Aurora PostgreSQL",
            "cache": "ElastiCache Redis" if self.cache else "disabled",
        }
    
    def delete_company(self, company_id: str) -> bool:
        """Delete all chunks for a company."""
        success = self.vector_store.delete_company(company_id)
        if success and self.cache:
            self.cache.invalidate_company(company_id)
        return success