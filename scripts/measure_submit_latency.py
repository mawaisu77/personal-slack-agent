#!/usr/bin/env python3
"""
T-056: rough latency sample for task submission (or any local callable).

Example:
  MAX_CONCURRENT_TASKS_PER_USER=0 python scripts/measure_submit_latency.py

For real Slack p95 ack &lt; 2s, run against staging with signed Slack requests (not included here).
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from personal_ai.config.settings import reset_settings_cache


def _one_submit() -> float:
    from unittest.mock import MagicMock

    import fakeredis

    from personal_ai.orchestrator.dispatch import OrchestratorDispatchService
    from personal_ai.queue.redis_queue import RedisJobQueue
    from personal_ai.state.models import TaskType

    session = MagicMock()
    session.scalar.return_value = 0
    r = fakeredis.FakeRedis(decode_responses=True)
    q = RedisJobQueue(r)
    svc = OrchestratorDispatchService(session, q)
    svc.register_handler("web", lambda job: {"ok": True})

    t0 = time.perf_counter()
    svc.submit_task(user_id="U-bench", task_type=TaskType.WEB, payload={"goal": "x"})
    return time.perf_counter() - t0


def main() -> None:
    reset_settings_cache()
    n = 40
    workers = 8
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_one_submit) for _ in range(n)]
        latencies = [f.result() for f in as_completed(futures)]
    latencies.sort()
    p95 = latencies[int(0.95 * (len(latencies) - 1))]
    med = statistics.median(latencies) * 1000
    p95_ms = p95 * 1000
    mx = max(latencies) * 1000
    print(f"samples={n} workers={workers} p50={med:.2f}ms p95={p95_ms:.2f}ms max={mx:.2f}ms")


if __name__ == "__main__":
    main()
