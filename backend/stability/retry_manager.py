from __future__ import annotations

from time import sleep


def retry_operation(
    operation,
    *args,
    retries: int = 2,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    delay_seconds: float = 0.2,
    **kwargs,
):
    """Retry transient operations a limited number of times."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            return operation(*args, **kwargs)
        except retry_exceptions as exc:
            last_error = exc
            if attempt == retries:
                raise
            sleep(delay_seconds)
    if last_error:
        raise last_error
