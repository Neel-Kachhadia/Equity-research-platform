"""
EREBUS · Redis Cache (ElastiCache)
===================================
Caches embeddings and query results for faster retrieval.
"""

import json
import logging
from typing import Optional, List, Dict, Any

from core.redis_client import cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Redis-based cache for embeddings and search results.
    Uses ElastiCache for low-latency retrieval.
    """
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl  # 1 hour default
    
    def _embedding_key(self, text_hash: str) -> str:
        return f"emb:{text_hash}"
    
    def _query_key(self, query: str, company_id: Optional[str], top_k: int) -> str:
        import hashlib
        key = f"{query}_{company_id}_{top_k}"
        return f"query:{hashlib.md5(key.encode()).hexdigest()}"
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = self._embedding_key(text_hash)
        cached = cache_get(key)
        if cached:
            logger.debug("[Cache] Embedding hit: %s", text_hash[:8])
            return json.loads(cached)
        return None
    
    def set_embedding(self, text: str, embedding: List[float]) -> bool:
        """Cache embedding for text."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = self._embedding_key(text_hash)
        return cache_set(key, json.dumps(embedding), ttl=self.ttl * 24)  # 24h for embeddings
    
    def get_query_results(
        self,
        query: str,
        company_id: Optional[str],
        top_k: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        key = self._query_key(query, company_id, top_k)
        cached = cache_get(key)
        if cached:
            logger.debug("[Cache] Query hit: %s", key[:20])
            return json.loads(cached)
        return None
    
    def set_query_results(
        self,
        query: str,
        company_id: Optional[str],
        top_k: int,
        results: List[Dict[str, Any]],
    ) -> bool:
        """Cache search results."""
        key = self._query_key(query, company_id, top_k)
        return cache_set(key, json.dumps(results, default=str), ttl=self.ttl)
    
    def invalidate_company(self, company_id: str) -> int:
        """Invalidate all cached queries for a company."""
        from core.redis_client import cache_invalidate_pattern
        return cache_invalidate_pattern(f"query:*{company_id}*")
    
    def clear_all(self) -> None:
        """Clear all RAG cache."""
        from core.redis_client import cache_invalidate_pattern
        cache_invalidate_pattern("emb:*")
        cache_invalidate_pattern("query:*")
        logger.info("[Cache] Cleared all RAG cache")