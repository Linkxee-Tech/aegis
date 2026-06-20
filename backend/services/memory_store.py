"""
Persistent memory storage backed by PostgreSQL + pgvector.

Data-access layer for the `memory_records` table. Schema creation is handled
by `backend/services/db.py`'s `run_migrations()` which runs on startup —
this module only needs to connect to an already-initialised database.
"""

import json
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg

from backend.config.settings import get_settings
from backend.services.cache import get_cache

logger = logging.getLogger("aegis.memory_store")
settings = get_settings()
CACHE_KEY = "memory:records:snapshot"


def _parse_embedding(text: str | None) -> list[float]:
    if not text:
        return []
    cleaned = text.strip().strip("[]")
    if not cleaned:
        return []
    return [float(part) for part in cleaned.split(",") if part]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


class MemoryStore:
    """Async data-access layer for the memory_records table."""

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        self._pool: asyncpg.Pool | None = None
        self._cache = get_cache()

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=10)
            logger.info("MemoryStore connected")

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def search_similar(self, embedding: list[float], *, top_k: int = 3) -> list[dict[str, Any]]:
        """Return the top_k closest stored incidents by cosine similarity, highest first."""
        await self.connect()
        assert self._pool is not None

        vector_literal = f"[{','.join(str(x) for x in embedding)}]"
        try:
            rows = await self._pool.fetch(
                """
                SELECT id, incident_title, root_cause, fix_applied, occurrences, last_seen,
                       embedding::text AS embedding_text,
                       1 - (embedding <=> $1::vector) AS similarity
                FROM memory_records
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                vector_literal,
                top_k,
            )
            records = [
                {
                    "id": str(row["id"]),
                    "incidentTitle": row["incident_title"],
                    "rootCause": row["root_cause"],
                    "fixApplied": json.loads(row["fix_applied"]),
                    "occurrences": row["occurrences"],
                    "lastSeen": row["last_seen"].isoformat(),
                    "embedding": _parse_embedding(row["embedding_text"]),
                    "similarity": float(row["similarity"]),
                }
                for row in rows
            ]
            await self._cache.set_json(CACHE_KEY, records, ttl_seconds=24 * 60 * 60)
            return [
                {key: value for key, value in record.items() if key != "embedding"}
                for record in records
            ]
        except Exception:
            logger.warning("Primary memory similarity search failed; using Redis snapshot fallback")
            cached = await self._cache.get_json(CACHE_KEY) or []
            ranked = []
            for record in cached:
                similarity = _cosine_similarity(embedding, record.get("embedding", []))
                ranked.append({**record, "similarity": similarity})
            ranked.sort(key=lambda item: item["similarity"], reverse=True)
            return [
                {
                    "id": record["id"],
                    "incidentTitle": record["incidentTitle"],
                    "rootCause": record["rootCause"],
                    "fixApplied": record["fixApplied"],
                    "occurrences": record["occurrences"],
                    "lastSeen": record["lastSeen"],
                    "similarity": float(record["similarity"]),
                }
                for record in ranked[:top_k]
            ]

    async def upsert_record(
        self,
        *,
        incident_title: str,
        root_cause: str,
        fix_applied: list[dict[str, Any]],
        embedding: list[float],
    ) -> str:
        """
        Store a new incident resolution, or bump the occurrence count of an
        existing near-identical record (similarity >= memory_similarity_threshold).
        """
        await self.connect()
        assert self._pool is not None

        existing = await self.search_similar(embedding, top_k=1)
        if existing and existing[0]["similarity"] >= settings.memory_similarity_threshold:
            record_id = existing[0]["id"]
            await self._pool.execute(
                """
                UPDATE memory_records
                SET occurrences = occurrences + 1, last_seen = $2
                WHERE id = $1
                """,
                uuid.UUID(record_id),
                datetime.now(timezone.utc),
            )
            await self.list_all()
            return record_id

        record_id = str(uuid.uuid4())
        vector_literal = f"[{','.join(str(x) for x in embedding)}]"
        await self._pool.execute(
            """
            INSERT INTO memory_records
                (id, incident_title, root_cause, fix_applied, embedding, occurrences, last_seen)
            VALUES ($1, $2, $3, $4, $5::vector, 1, $6)
            """,
            uuid.UUID(record_id),
            incident_title,
            root_cause,
            json.dumps(fix_applied),
            vector_literal,
            datetime.now(timezone.utc),
        )
        await self.list_all()
        return record_id

    async def list_all(self) -> list[dict[str, Any]]:
        await self.connect()
        assert self._pool is not None
        try:
            rows = await self._pool.fetch(
                """
                SELECT id, incident_title, root_cause, fix_applied, occurrences, last_seen, embedding::text AS embedding_text
                FROM memory_records
                ORDER BY last_seen DESC
                """
            )
            records = [
                {
                    "id": str(row["id"]),
                    "incidentTitle": row["incident_title"],
                    "rootCause": row["root_cause"],
                    "fixApplied": json.loads(row["fix_applied"]),
                    "occurrences": row["occurrences"],
                    "lastSeen": row["last_seen"].isoformat(),
                    "embedding": _parse_embedding(row["embedding_text"]),
                }
                for row in rows
            ]
            await self._cache.set_json(CACHE_KEY, records, ttl_seconds=24 * 60 * 60)
            return [
                {key: value for key, value in record.items() if key != "embedding"}
                for record in records
            ]
        except Exception:
            logger.warning("Primary memory listing failed; using Redis snapshot fallback")
            cached = await self._cache.get_json(CACHE_KEY) or []
            return [
                {
                    "id": record["id"],
                    "incidentTitle": record["incidentTitle"],
                    "rootCause": record["rootCause"],
                    "fixApplied": record["fixApplied"],
                    "occurrences": record["occurrences"],
                    "lastSeen": record["lastSeen"],
                }
                for record in cached
            ]
