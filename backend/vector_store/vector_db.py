"""
Vector DB — SQLite-backed vector index with cosine similarity search.

Stores text chunks + embeddings in SQLite. Embeddings are stored as
BLOBs (float32 arrays). At query time, loads all embeddings into
memory for fast cosine similarity computation.

For ~500 vectors × 1536 floats = ~3MB, this is very efficient.
"""

import json
import math
import os
import sqlite3
import struct
from typing import List, Dict, Optional, Tuple


class VectorDB:
    """SQLite-based vector database with cosine similarity search."""

    DIMENSIONS = 1536
    TABLE_NAME = "chunks"

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open the database connection and ensure the table exists."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_table()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _create_table(self):
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_text TEXT NOT NULL,
                source_file TEXT NOT NULL,
                heading_path TEXT DEFAULT '',
                category TEXT DEFAULT '',
                char_count INTEGER DEFAULT 0,
                embedding BLOB NOT NULL
            )
        """)
        self._conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_category
            ON {self.TABLE_NAME}(category)
        """)
        self._conn.commit()

    def insert(self, chunks: List[Dict], embeddings: List[List[float]]):
        """Insert chunks and their embeddings into the database."""
        assert len(chunks) == len(embeddings), "Chunks and embeddings must match"

        rows = []
        for chunk, emb in zip(chunks, embeddings):
            blob = self._pack_embedding(emb)
            rows.append((
                chunk.get("text", ""),
                chunk.get("source_file", ""),
                chunk.get("heading_path", ""),
                chunk.get("category", ""),
                chunk.get("char_count", 0),
                blob,
            ))

        self._conn.executemany(
            f"""INSERT INTO {self.TABLE_NAME}
                (chunk_text, source_file, heading_path, category, char_count, embedding)
                VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )
        self._conn.commit()

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        category_filter: Optional[str] = None,
        min_similarity: float = 0.3,
    ) -> List[Dict]:
        """
        Search for chunks most similar to the query embedding.

        Returns list of {chunk_text, source_file, heading_path, similarity, ...}
        """
        # Load all embeddings (cached in memory for speed)
        rows = self._load_all()

        if not rows:
            return []

        # Compute cosine similarity
        scored = []
        query_vec = query_embedding
        query_norm = math.sqrt(sum(x * x for x in query_vec))

        if query_norm == 0:
            return []

        for row in rows:
            emb = self._unpack_embedding(row["embedding_blob"])
            if category_filter and row["category"] != category_filter:
                continue

            similarity = self._cosine_similarity(query_vec, emb, query_norm)
            if similarity >= min_similarity:
                scored.append({
                    "chunk_text": row["chunk_text"],
                    "source_file": row["source_file"],
                    "heading_path": row["heading_path"],
                    "category": row["category"],
                    "similarity": round(similarity, 4),
                    "char_count": row["char_count"],
                })

        scored.sort(key=lambda x: -x["similarity"])
        return scored[:top_k]

    def search_by_keywords(
        self,
        keywords: List[str],
        top_k: int = 10,
        category_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fallback keyword search when embeddings are not available.
        Uses SQLite LIKE matching.
        """
        results = []
        seen_ids = set()

        for kw in keywords:
            kw_clean = kw.strip().lower()
            if len(kw_clean) < 3:
                continue

            sql = f"""
                SELECT id, chunk_text, source_file, heading_path, category, char_count
                FROM {self.TABLE_NAME}
                WHERE LOWER(chunk_text) LIKE ?
            """
            params = [f"%{kw_clean}%"]

            if category_filter:
                sql += " AND category = ?"
                params.append(category_filter)

            sql += " LIMIT ?"
            params.append(top_k)

            cursor = self._conn.execute(sql, params)
            for row in cursor:
                row_id = row[0]
                if row_id not in seen_ids:
                    seen_ids.add(row_id)
                    results.append({
                        "chunk_text": row[1],
                        "source_file": row[2],
                        "heading_path": row[3],
                        "category": row[4],
                        "similarity": 0.5,  # Dummy score for keyword match
                        "char_count": row[5],
                    })

        # Sort by number of keyword matches (approximate)
        results.sort(key=lambda r: sum(
            1 for kw in keywords if kw.lower() in r["chunk_text"].lower()
        ), reverse=True)

        return results[:top_k]

    def get_stats(self) -> Dict:
        """Return database statistics."""
        cursor = self._conn.execute(f"""
            SELECT category, COUNT(*) as cnt
            FROM {self.TABLE_NAME}
            GROUP BY category
            ORDER BY cnt DESC
        """)
        categories = {row[0]: row[1] for row in cursor}

        total = self._conn.execute(
            f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
        ).fetchone()[0]

        return {
            "total_chunks": total,
            "categories": categories,
            "dimensions": self.DIMENSIONS,
        }

    def clear(self):
        """Delete all chunks from the database."""
        self._conn.execute(f"DELETE FROM {self.TABLE_NAME}")
        self._conn.commit()

    # ── Internal helpers ────────────────────────────────────────────

    def _load_all(self) -> List[Dict]:
        """Load all rows from the database (cached for performance)."""
        cursor = self._conn.execute(
            f"SELECT id, chunk_text, source_file, heading_path, category, char_count, embedding "
            f"FROM {self.TABLE_NAME}"
        )
        return [
            {
                "id": row[0],
                "chunk_text": row[1],
                "source_file": row[2],
                "heading_path": row[3],
                "category": row[4],
                "char_count": row[5],
                "embedding_blob": row[6],
            }
            for row in cursor
        ]

    @staticmethod
    def _pack_embedding(embedding: List[float]) -> bytes:
        """Pack a float32 list into a binary blob."""
        return struct.pack(f"{len(embedding)}f", *embedding)

    @staticmethod
    def _unpack_embedding(blob: bytes) -> List[float]:
        """Unpack a binary blob into a float32 list."""
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob))

    @staticmethod
    def _cosine_similarity(
        a: List[float], b: List[float], a_norm: float = None
    ) -> float:
        """Compute cosine similarity between two vectors."""
        if a_norm is None:
            a_norm = math.sqrt(sum(x * x for x in a))
        b_norm = math.sqrt(sum(x * x for x in b))
        if a_norm == 0 or b_norm == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        return dot / (a_norm * b_norm)
