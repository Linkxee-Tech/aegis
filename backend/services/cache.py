"""
Redis-backed cache used for two things in Aegis:
  1. Caching recent metric baselines so the Detective Agent doesn't recompute
     a 7-day rolling average on every poll cycle.
  2. Tracking pending approval requests with a TTL, so an unanswered approval
     expires automatically rather than blocking an incident forever.
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

from backend.config.settings import get_settings

logger = logging.getLogger("aegis.cache")
settings = get_settings()


class CacheService:
    def __init__(self, url: str | None = None) -> None:
        self._url = url or settings.redis_url
        self._client: redis.Redis | None = None

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._url, decode_responses=True)
        return self._client

    async def get_json(self, key: str) -> Any | None:
        raw = await self._get_client().get(key)
        return json.loads(raw) if raw else None

    async def set_json(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        await self._get_client().set(key, json.dumps(value), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._get_client().delete(key)

    async def set_pending_approval(self, incident_id: str, payload: dict[str, Any]) -> None:
        await self.set_json(
            f"approval:{incident_id}",
            payload,
            ttl_seconds=settings.approval_timeout_seconds,
        )

    async def get_pending_approval(self, incident_id: str) -> dict[str, Any] | None:
        return await self.get_json(f"approval:{incident_id}")

    async def clear_pending_approval(self, incident_id: str) -> None:
        await self.delete(f"approval:{incident_id}")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


_cache: CacheService | None = None


def get_cache() -> CacheService:
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
