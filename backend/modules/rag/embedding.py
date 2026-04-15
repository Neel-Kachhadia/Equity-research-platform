from __future__ import annotations
"""
EREBUS · Embedding Generator
=============================
Generates vector embeddings for text chunks.
Supports OpenAI, Cohere, and local models.
"""

import os
import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from .chunking import TextChunk

logger = logging.getLogger(__name__)


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"


@dataclass
class EmbeddedChunk:
    """Text chunk with its embedding vector."""
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]


class EmbeddingGenerator:
    """
    Generate embeddings using various providers.
    Caches embeddings to avoid redundant API calls.
    """
    
    def __init__(
        self,
        provider: EmbeddingProvider = EmbeddingProvider.HUGGINGFACE,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        batch_size: int = 100,
    ):
        self.provider = provider
        self.model = model or self._get_default_model()
        self.api_key = api_key or self._get_api_key()
        self.batch_size = batch_size
        self._client = None
        self._initialize_client()
        
        # Simple in-memory cache
        self._cache: Dict[str, List[float]] = {}
    
    def _get_default_model(self) -> str:
        defaults = {
            EmbeddingProvider.OPENAI: "text-embedding-3-small",
            EmbeddingProvider.COHERE: "embed-english-v3.0",
            EmbeddingProvider.HUGGINGFACE: "sentence-transformers/all-MiniLM-L6-v2",
            EmbeddingProvider.OLLAMA: "nomic-embed-text",
        }
        return defaults.get(self.provider, "text-embedding-3-small")
    
    def _get_api_key(self) -> Optional[str]:
        key_map = {
            EmbeddingProvider.OPENAI: "OPENAI_API_KEY",
            EmbeddingProvider.COHERE: "COHERE_API_KEY",
            EmbeddingProvider.HUGGINGFACE: "HUGGINGFACE_API_KEY",
            EmbeddingProvider.OLLAMA: None,
        }
        env_var = key_map.get(self.provider)
        return os.getenv(env_var) if env_var else None
    
    def _initialize_client(self):
        """Initialize provider-specific client."""
        try:
            if self.provider == EmbeddingProvider.OPENAI:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                
            elif self.provider == EmbeddingProvider.COHERE:
                import cohere
                self._client = cohere.Client(api_key=self.api_key)
                
            elif self.provider == EmbeddingProvider.HUGGINGFACE:
                from sentence_transformers import SentenceTransformer
                self._client = SentenceTransformer(self.model)
                
            elif self.provider == EmbeddingProvider.OLLAMA:
                import requests
                self._client = requests.Session()
                self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                
        except ImportError as e:
            logger.error(f"Failed to import {self.provider} client: {e}")
            self._client = None
            raise
    
    def embed_chunks(
        self,
        chunks: List[TextChunk],
        show_progress: bool = False,
    ) -> List[EmbeddedChunk]:
        """
        Generate embeddings for multiple chunks.
        
        Args:
            chunks: List of TextChunk objects
            show_progress: Whether to show progress bar
            
        Returns:
            List of EmbeddedChunk objects
        """
        from .chunking import TextChunk
        
        embedded_chunks = []
        texts = [chunk.text for chunk in chunks]
        
        # Check cache first
        uncached_indices = []
        uncached_texts = []
        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                embedded_chunks.append(
                    EmbeddedChunk(
                        chunk_id=chunks[i].chunk_id,
                        text=text,
                        embedding=self._cache[cache_key],
                        metadata=chunks[i].metadata,
                    )
                )
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)
        
        if not uncached_texts:
            logger.info(f"[Embedding] All {len(chunks)} chunks cached")
            return embedded_chunks
        
        logger.info(f"[Embedding] Generating embeddings for {len(uncached_texts)} chunks")
        
        # Process in batches
        for batch_start in range(0, len(uncached_texts), self.batch_size):
            batch_texts = uncached_texts[batch_start:batch_start + self.batch_size]
            batch_embeddings = self._embed_batch(batch_texts)
            
            for i, embedding in enumerate(batch_embeddings):
                original_idx = uncached_indices[batch_start + i]
                text = texts[original_idx]
                
                # Cache the embedding
                cache_key = self._cache_key(text)
                self._cache[cache_key] = embedding
                
                embedded_chunks.append(
                    EmbeddedChunk(
                        chunk_id=chunks[original_idx].chunk_id,
                        text=text,
                        embedding=embedding,
                        metadata=chunks[original_idx].metadata,
                    )
                )
        
        # Sort back to original order
        embedded_chunks.sort(key=lambda x: x.chunk_id)
        
        return embedded_chunks
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        cache_key = self._cache_key(query)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        embedding = self._embed_batch([query])[0]
        self._cache[cache_key] = embedding
        return embedding
    
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            if self.provider == EmbeddingProvider.OPENAI:
                return self._embed_openai(texts)
            elif self.provider == EmbeddingProvider.COHERE:
                return self._embed_cohere(texts)
            elif self.provider == EmbeddingProvider.HUGGINGFACE:
                return self._embed_huggingface(texts)
            elif self.provider == EmbeddingProvider.OLLAMA:
                return self._embed_ollama(texts)
        except Exception as e:
            logger.error(f"[Embedding] Failed: {e}")
            raise
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI embeddings."""
        response = self._client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    def _embed_cohere(self, texts: List[str]) -> List[List[float]]:
        """Cohere embeddings."""
        response = self._client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document",
        )
        return response.embeddings
    
    def _embed_huggingface(self, texts: List[str]) -> List[List[float]]:
        """Local HuggingFace embeddings."""
        embeddings = self._client.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()
    
    def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Ollama local embeddings."""
        import json
        
        embeddings = []
        for text in texts:
            response = self._client.post(
                f"{self.ollama_host}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            data = response.json()
            embeddings.append(data["embedding"])
        return embeddings
    
    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        import hashlib
        return hashlib.md5(f"{self.provider}:{self.model}:{text}".encode()).hexdigest()


def create_embeddings(
    chunks: List[TextChunk],
    provider: str = "huggingface",
    model: Optional[str] = None,
) -> List[EmbeddedChunk]:
    """Convenience function to create embeddings."""
    generator = EmbeddingGenerator(
        provider=EmbeddingProvider(provider),
        model=model,
    )
    return generator.embed_chunks(chunks)