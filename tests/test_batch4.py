from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import fakeredis

from personal_ai.observability.replay_store import ReplayTraceStore
from personal_ai.orchestrator.dispatch import OrchestratorDispatchService
from personal_ai.queue.redis_queue import RedisJobQueue
from personal_ai.queue.retry import RetryPolicy, run_with_retry
from personal_ai.queue.schemas import JobPayload
from personal_ai.state.models import TaskStatus, TaskType
from personal_ai.voice.outbound import OutboundCallService
from personal_ai.voice.provider import NoopVoiceProvider
from personal_ai.web.capture import capture_page_state


def test_retry_succeeds_after_failures() -> None:
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise RuntimeError("boom")
        return "ok"

    with patch("time.sleep", autospec=True):
        out = run_with_retry(flaky, policy=RetryPolicy(max_attempts=3, base_delay_seconds=0))
    assert out == "ok"
    assert state["n"] == 3


def test_dispatch_submit_and_route() -> None:
    session = MagicMock()
    q = RedisJobQueue(fakeredis.FakeRedis(decode_responses=True))
    svc = OrchestratorDispatchService(session, q)
    handled: dict[str, str] = {}

    def handler(job: JobPayload) -> dict[str, str]:
        handled["type"] = job.type
        return {"ok": "1"}

    svc.register_handler("web", handler)
    task = svc.submit_task(
        user_id="U1",
        task_type=TaskType.WEB,
        payload={"goal": "open"},
        priority=2,
    )
    assert task.status == TaskStatus.PENDING
    job = q.dequeue(timeout_seconds=1)
    assert job is not None
    out = svc.dispatch(job)
    assert out["ok"] == "1"
    assert handled["type"] == "web"


def test_capture_truncates_dom() -> None:
    page = MagicMock()
    page.content.return_value = "x" * 20
    page.screenshot.return_value = b"png-bytes"
    cap = capture_page_state(page, max_dom_chars=5)
    assert cap["truncated"] is True
    assert cap["dom"] == "xxxxx"
    assert cap["screenshot_png"] == b"png-bytes"


def test_outbound_call_service_noop() -> None:
    svc = OutboundCallService(NoopVoiceProvider())
    res = svc.place_call("+15555550123", metadata={"task_id": "t1"})
    assert res.success is True
    assert res.call_id is not None


def test_replay_trace_store_writes_jsonl(tmp_path: Path) -> None:
    store = ReplayTraceStore(tmp_path)
    p = store.append(task_id=str(uuid.uuid4()), step=1, payload={"a": 1}, version="v1")
    text = p.read_text(encoding="utf-8")
    assert '"version":"v1"' in text
    assert '"step":1' in text
