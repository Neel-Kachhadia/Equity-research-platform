"""
EREBUS · RAG Retriever (with Redis Cache)
==========================================
Retrieves relevant context with caching and reranking.
"""

import logging
from typing import List, Dict, Any, Optional

from .embedding import EmbeddingGenerator, EmbeddingProvider
from .vector_store import get_vector_store
from .cache import EmbeddingCache

logger = logging.getLogger(__name__)


class RagRetriever:
    """
    Retrieve relevant document chunks for a query.
    Uses Redis cache for embeddings and query results.
    """
    
    def __init__(
        self,
        embedding_provider: str = "huggingface",
        embedding_model: Optional[str] = None,
        use_reranking: bool = True,
        use_cache: bool = True,
    ):
        self.embedding_generator = EmbeddingGenerator(
            provider=EmbeddingProvider(embedding_provider),
            model=embedding_model,
        )
        self.vector_store = get_vector_store()
        self.cache = EmbeddingCache() if use_cache else None
        self.use_reranking = use_reranking
        self.use_cache = use_cache
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        company_id: Optional[str] = None,
        min_similarity: float = 0.5,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            company_id: Optional company filter
            min_similarity: Minimum similarity threshold
            force_refresh: Skip cache
            
        Returns:
            List of retrieved chunks with text and metadata
        """
        # Check cache first
        if self.use_cache and not force_refresh:
            cached = self.cache.get_query_results(query, company_id, top_k)
            if cached:
                logger.info("[Retriever] Cache hit for query")
                return cached
        
        # Generate query embedding (with cache)
        if self.use_cache:
            cached_emb = self.cache.get_embedding(query)
            if cached_emb:
                query_embedding = cached_emb
                logger.debug("[Retriever] Embedding cache hit")
            else:
                query_embedding = self.embedding_generator.embed_query(query)
                self.cache.set_embedding(query, query_embedding)
        else:
            query_embedding = self.embedding_generator.embed_query(query)
        
        # Retrieve candidates
        fetch_k = top_k * 2 if self.use_reranking else top_k
        candidates = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=fetch_k,
            company_id=company_id,
            min_similarity=min_similarity,
        )
        
        if not candidates:
            logger.warning(f"[Retriever] No results for query: {query[:50]}...")
            return []
        
        # Rerank if enabled
        if self.use_reranking and len(candidates) > top_k:
            candidates = self._rerank(query, candidates, top_k)
        else:
            candidates = candidates[:top_k]
        
        # Cache results
        if self.use_cache:
            self.cache.set_query_results(query, company_id, top_k, candidates)
        
        logger.info(f"[Retriever] Retrieved {len(candidates)} chunks")
        return candidates
    
    def _rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Rerank candidates using section priority and keyword overlap."""
        query_terms = set(query.lower().split())
        
        def score_candidate(candidate: Dict[str, Any]) -> float:
            score = candidate.get("similarity", 0)
            
            # Boost based on section type
            section = candidate.get("section", "").lower()
            if "md&a" in section or "discussion" in section:
                score += 0.15
            elif "risk" in section:
                score += 0.10
            elif "financial" in section or "statement" in section:
                score += 0.08
            elif "quarterly" in section or "earnings" in section:
                score += 0.12
            
            # Boost based on chunk type
            if candidate.get("chunk_type") == "table":
                score += 0.05
            
            # Boost based on keyword overlap
            text = candidate.get("text", "").lower()
            text_terms = set(text.split())
            overlap = len(query_terms & text_terms) / max(len(query_terms), 1)
            score += overlap * 0.20
            
            return score
        
        candidates.sort(key=score_candidate, reverse=True)
        return candidates[:top_k]
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        company_id: Optional[str] = None,
        combine: bool = True,
        force_refresh: bool = False,
    ) -> str | List[str]:
        """
        Retrieve and format context for LLM.
        """
        results = self.retrieve(query, top_k, company_id, force_refresh=force_refresh)
        
        if combine:
            contexts = []
            for i, r in enumerate(results, 1):
                section = r.get("section", "Document")
                contexts.append(f"[{i}] {section}:\n{r['text']}\n")
            return "\n".join(contexts)
        else:
            return [r["text"] for r in results]
    
    def invalidate_cache(self, company_id: Optional[str] = None) -> None:
        """Invalidate cache for a company or all."""
        if self.cache:
            if company_id:
                self.cache.invalidate_company(company_id)
            else:
                self.cache.clear_all()


def retrieve_context(
    query: str,
    top_k: int = 5,
    company_id: Optional[str] = None,
    provider: str = "huggingface",
) -> str:
    """Convenience function to retrieve context."""
    retriever = RagRetriever(embedding_provider=provider)
    return retriever.retrieve_context(query, top_k, company_id, combine=True)