"""
Embedding Client — generates embeddings via OpenAI text-embedding-3-small.

Supports batching for efficiency and caching to avoid redundant API calls.
"""

import asyncio
from typing import List

import httpx


class EmbeddingClient:
    """Generates text embeddings using OpenAI's embedding API."""

    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    MAX_BATCH_SIZE = 50  # OpenAI allows up to 2048 inputs per request

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(60.0),
        )

    async def close(self):
        await self._http.aclose()

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Automatically batches to respect API limits.
        """
        if not texts:
            return []

        all_embeddings = []
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i:i + self.MAX_BATCH_SIZE]
            batch_embeddings = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        results = await self.embed([text])
        return results[0] if results else []

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Send a single batch request to the embedding API."""
        body = {
            "model": self.MODEL,
            "input": texts,
            "encoding_format": "float",
        }

        resp = await self._http.post("/embeddings", json=body)
        resp.raise_for_status()
        data = resp.json()

        # Sort by index to preserve order
        items = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in items]

    @staticmethod
    async def build_from_config(api_key: str, base_url: str = None) -> "EmbeddingClient":
        """Factory: create an EmbeddingClient from config."""
        return EmbeddingClient(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
        )
