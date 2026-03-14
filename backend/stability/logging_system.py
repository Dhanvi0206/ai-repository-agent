from __future__ import annotations

import logging
from pathlib import Path


LOG_PATH = Path("workspace") / "logs" / "system.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("ai_repository_agent")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(component)s | %(event_type)s | %(message)s"
    )
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)


def log_event(component: str, event_type: str, message: str, **context) -> None:
    structured_message = message
    if context:
        structured_message = f"{message} | context={context}"
    _logger.info(
        structured_message,
        extra={"component": component, "event_type": event_type},
    )
