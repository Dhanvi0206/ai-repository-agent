from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AppError(Exception):
    message: str
    error_type: str = "ApplicationError"
    status_code: int = 400
    details: dict | None = None

    def to_response(self) -> dict:
        return format_error_response(self)


def format_error_response(error: Exception) -> dict:
    if isinstance(error, AppError):
        return {
            "status": "error",
            "message": error.message,
            "error_type": error.error_type,
            "details": error.details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": "error",
        "message": str(error),
        "error_type": error.__class__.__name__,
        "details": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
