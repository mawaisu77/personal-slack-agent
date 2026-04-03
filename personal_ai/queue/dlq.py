"""Dead-letter queue for poison / exhausted-retry jobs (T-006)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from personal_ai.queue.schemas import JobPayload


class DeadLetterQueue:
    """
    Redis LIST of JSON entries: task_id, error, job snapshot, enqueued_at.
    Use ``LRANGE`` for inspection (CLI / admin later).
    """

    def __init__(self, client: Any, *, list_key: str = "queue:dlq") -> None:
        self._r = client
        self._key = list_key

    def push(
        self,
        *,
        task_id: uuid.UUID,
        last_error: str,
        job: JobPayload | None = None,
    ) -> None:
        entry = {
            "task_id": str(task_id),
            "last_error": last_error,
            "enqueued_at": time.time(),
            "job": job.model_dump(mode="json") if job is not None else None,
        }
        self._r.lpush(self._key, json.dumps(entry, separators=(",", ":")))

    def list_recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        """Return newest-first DLQ entries (up to ``limit``)."""
        raw = self._r.lrange(self._key, 0, max(0, limit - 1))
        out: list[dict[str, Any]] = []
        for item in raw:
            s = item.decode("utf-8") if isinstance(item, bytes) else item
            out.append(json.loads(s))
        return out
