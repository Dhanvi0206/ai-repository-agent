from __future__ import annotations

from collections import defaultdict, deque
from time import time

from backend.stability.error_handler import AppError


def validate_repo_url(repo_url: str) -> str:
    normalized = (repo_url or "").strip()
    if not normalized:
        raise AppError(
            "Repository URL is required.",
            error_type="InvalidRepository",
            status_code=400,
        )
    if not normalized.startswith("https://github.com/"):
        raise AppError(
            "Repository URL must start with https://github.com/.",
            error_type="InvalidRepository",
            status_code=400,
        )
    return normalized


def validate_pagination(page: int, limit: int) -> tuple[int, int]:
    if page < 1:
        raise AppError("Page must be greater than 0.", error_type="InvalidPagination")
    if limit < 1 or limit > 100:
        raise AppError(
            "Limit must be between 1 and 100.",
            error_type="InvalidPagination",
        )
    return page, limit


class RateLimiter:
    """Simple in-memory fixed-window rate limiter."""

    def __init__(self, max_requests: int = 10, period_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self._requests: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time()
        bucket = self._requests[key]
        while bucket and now - bucket[0] > self.period_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise AppError(
                "Rate limit exceeded. Please retry later.",
                error_type="RateLimitExceeded",
                status_code=429,
                details={"max_requests": self.max_requests, "period_seconds": self.period_seconds},
            )
        bucket.append(now)
