from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from personal_ai.observability.logging import get_logger

log = get_logger(__name__)
T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 5.0
    multiplier: float = 2.0


def _backoff(policy: RetryPolicy, attempt: int) -> float:
    delay = policy.base_delay_seconds * (policy.multiplier ** max(0, attempt - 1))
    return min(policy.max_delay_seconds, delay)


def run_with_retry(
    fn: Callable[[], T],
    *,
    policy: RetryPolicy | None = None,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """
    Run fn with exponential backoff retries (T-005).
    Logs attempt count and sleeps between failures.
    """
    p = policy or RetryPolicy()
    last: Exception | None = None
    for attempt in range(1, p.max_attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            log.warning(
                "job_attempt_failed",
                attempt=attempt,
                max_attempts=p.max_attempts,
                error=str(exc),
            )
            if attempt >= p.max_attempts:
                break
            if on_retry is not None:
                on_retry(attempt, exc)
            time.sleep(_backoff(p, attempt))
    assert last is not None
    raise last
