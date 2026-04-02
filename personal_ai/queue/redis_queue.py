"""
Redis job queue: ZSET priority + FIFO (T-004).

**Algorithm**

- Members are opaque message IDs (UUID strings).
- Payloads live in Redis hashes ``{data_prefix}{id}`` field ``body`` (JSON text).
- ``BZPOPMIN`` pops the smallest score: higher ``JobPayload.priority`` dequeues first.

::

    score = (MAX_PRIORITY - clamp(priority, 0, MAX_PRIORITY)) * PRIORITY_SLOT + time.time()

``PRIORITY_SLOT = 10**10`` separates priority bands; ``time.time()`` breaks ties FIFO
within the same priority (older jobs have a smaller timestamp).
"""

from __future__ import annotations

import math
import time
import uuid
from typing import TYPE_CHECKING

import redis

from personal_ai.queue.schemas import JobPayload

if TYPE_CHECKING:
    from redis.client import Redis

# Clamp job priority to [0, MAX_PRIORITY]; higher = more urgent.
MAX_PRIORITY = 99
PRIORITY_SLOT = 10**10


def _score(priority: int) -> float:
    p = max(0, min(int(priority), MAX_PRIORITY))
    return float((MAX_PRIORITY - p) * PRIORITY_SLOT + time.time())


class RedisJobQueue:
    """Blocking priority queue backed by Redis ZSET + HASH."""

    def __init__(
        self,
        client: Redis,
        *,
        zset_key: str = "queue:jobs",
        data_prefix: str = "queue:data:",
    ) -> None:
        self._r = client
        self._z = zset_key
        self._dp = data_prefix

    def enqueue(self, job: JobPayload) -> str:
        """Push job; returns message id."""
        mid = str(uuid.uuid4())
        body = job.to_redis_body()
        raw = body.decode("utf-8") if isinstance(body, bytes) else body
        sc = _score(job.priority)
        pipe = self._r.pipeline()
        pipe.hset(f"{self._dp}{mid}", mapping={"body": raw})
        pipe.zadd(self._z, {mid: sc})
        pipe.execute()
        return mid

    def dequeue(self, *, timeout_seconds: float = 5.0) -> JobPayload | None:
        """
        Block up to ``timeout_seconds`` for the next job.
        ``timeout_seconds == 0`` blocks indefinitely (Redis ``BZPOPMIN``).
        """
        tout = max(0, int(math.ceil(timeout_seconds)))
        result = self._r.bzpopmin([self._z], timeout=tout)
        if result is None:
            return None
        _key, member, _sc = result
        hkey = f"{self._dp}{member}"
        raw = self._r.hget(hkey, "body")
        self._r.delete(hkey)
        if raw is None:
            return None
        blob = raw.encode("utf-8") if isinstance(raw, str) else raw
        return JobPayload.from_redis_body(blob)


def get_redis_client(url: str) -> redis.Redis:
    return redis.from_url(url, decode_responses=True)
