"""
EREBUS · RAG Module (AWS Stack)
================================
Retrieval-Augmented Generation using:
    - AWS Aurora PostgreSQL (pgvector) for vector storage
    - AWS ElastiCache Redis for embedding/query caching
    - OpenAI/Cohere/HuggingFace for embeddings

Usage:
    from modules.rag import RagPipeline
    
    pipeline = RagPipeline()
    pipeline.index_documents(company_id="TCS", documents=[...])
    context = pipeline.retrieve_context("What was TCS revenue?")
"""

from .pipeline import RagPipeline
from .chunking import SemanticChunker, chunk_text
from .embedding import EmbeddingGenerator, create_embeddings
from .vector_store import VectorStore, get_vector_store
from .query import RagRetriever, retrieve_context
from .cache import EmbeddingCache

__all__ = [
    "RagPipeline",
    "SemanticChunker",
    "chunk_text",
    "EmbeddingGenerator",
    "create_embeddings",
    "VectorStore",
    "get_vector_store",
    "RagRetriever",
    "retrieve_context",
    "EmbeddingCache",
]