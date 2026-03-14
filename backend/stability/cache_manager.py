from __future__ import annotations

from datetime import datetime, timedelta, timezone


class CacheManager:
    """TTL-based in-memory cache manager for repository reports."""

    def __init__(self, ttl_minutes: int = 30) -> None:
        self.ttl = timedelta(minutes=ttl_minutes)
        self._cache: dict[str, dict] = {}

    def set(self, key: str, value: dict) -> None:
        self._cache[key] = {
            "value": value,
            "cached_at": datetime.now(timezone.utc),
        }

    def get(self, key: str) -> dict | None:
        cached = self._cache.get(key)
        if not cached:
            return None
        if datetime.now(timezone.utc) - cached["cached_at"] > self.ttl:
            self._cache.pop(key, None)
            return None
        return cached["value"]
