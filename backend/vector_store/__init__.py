"""
Vector Store — Knowledge base chunking, embedding, and vector search.

Provides semantic search over the automotive knowledge base for
injecting relevant context into agent execution prompts.
"""

from vector_store.chunker import KnowledgeBaseChunker
from vector_store.embedding import EmbeddingClient
from vector_store.vector_db import VectorDB

__all__ = ["KnowledgeBaseChunker", "EmbeddingClient", "VectorDB"]
