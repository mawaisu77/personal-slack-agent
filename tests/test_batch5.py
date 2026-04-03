from __future__ import annotations

import uuid
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from personal_ai.context_store.masked import MaskedContextStore, redact_json
from personal_ai.observability.replay_store import ReplayTraceStore
from personal_ai.queue.dlq import DeadLetterQueue
from personal_ai.queue.redis_queue import RedisJobQueue
from personal_ai.queue.schemas import JobPayload
from personal_ai.run.runner import AgentRunner
from personal_ai.slack_interface.tasks import submit_web_task_sync
from personal_ai.state.models import TaskStatus
from personal_ai.voice.phone import resolve_phone_e164
from personal_ai.web.executor import execute_action
from personal_ai.web.screenshot_storage import LocalScreenshotStorage


def test_dead_letter_queue_push_and_list() -> None:
    r = fakeredis.FakeRedis(decode_responses=True)
    dlq = DeadLetterQueue(r)
    tid = uuid.uuid4()
    job = JobPayload(task_id=tid, user_id="U1", type="web", payload={"a": 1})
    dlq.push(task_id=tid, last_error="boom", job=job)
    rows = dlq.list_recent(limit=5)
    assert len(rows) == 1
    assert rows[0]["task_id"] == str(tid)
    assert rows[0]["last_error"] == "boom"
    assert rows[0]["job"]["type"] == "web"


def test_resolve_phone_e164() -> None:
    assert resolve_phone_e164({"phone": "+15555550123"}) == "+15555550123"
    assert resolve_phone_e164({"phone": "(555) 555-0123"}) == "+15555550123"


def test_redact_json_masks_sensitive_keys() -> None:
    out = redact_json({"api_key": "secret", "profile": {"password": "x"}, "name": "Ada"})
    assert out["api_key"] == "***"
    assert out["name"] == "Ada"
    assert out["profile"]["password"] == "***"


def test_masked_context_store_get_redacts() -> None:
    row = MagicMock()
    row.value_json = {"token": "abc", "x": 1}
    inner = MagicMock()
    inner.get.return_value = row
    masked = MaskedContextStore(inner)
    out = masked.get(user_id="U1", context_key="k")
    assert out is not None
    assert out.value_json["token"] == "***"
    assert out.value_json["x"] == 1


def test_local_screenshot_storage_url(tmp_path) -> None:
    store = LocalScreenshotStorage(tmp_path, public_base_url="https://example.test")
    url = store.store_png(task_id="t1", name="s1", data=b"\x89PNG")
    assert url.startswith("https://example.test/screenshots/")
    assert "t1" in url


def test_execute_action_click_and_wait() -> None:
    page = MagicMock()
    loc = MagicMock()
    page.locator.return_value = loc
    loc.first.click.return_value = None
    loc.first.fill.return_value = None
    loc.first.scroll_into_view_if_needed.return_value = None
    loc.first.inner_text.return_value = "hello"

    r1 = execute_action(
        page,
        {"action": "click", "target": "button", "confidence": 1, "reason": "r"},
    )
    assert r1["ok"] is True

    r2 = execute_action(
        page,
        {"action": "wait", "target": "", "value": "0.01", "confidence": 1, "reason": "r"},
    )
    assert r2["ok"] is True
    page.wait_for_timeout.assert_called()

    r3 = execute_action(
        page,
        {"action": "extract", "target": "#x", "confidence": 1, "reason": "r"},
    )
    assert r3["detail"] == "hello"


def test_replay_trace_round_trip(tmp_path) -> None:
    tid = str(uuid.uuid4())
    store = ReplayTraceStore(tmp_path)
    store.append(task_id=tid, step=1, payload={"a": 1}, version="v1")
    lines = store.read_trace_lines(tid)
    assert len(lines) == 1
    assert lines[0]["step"] == 1
    assert lines[0]["payload"]["a"] == 1


def test_submit_web_task_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    tid = uuid.uuid4()

    def fake_submit(self, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        t = MagicMock()
        t.id = tid
        return t

    monkeypatch.setattr(
        "personal_ai.slack_interface.tasks.OrchestratorDispatchService.submit_task",
        fake_submit,
    )

    @contextmanager
    def noop_scope():  # type: ignore[no-untyped-def]
        yield MagicMock()

    monkeypatch.setattr("personal_ai.slack_interface.tasks.session_scope", noop_scope)
    monkeypatch.setattr(
        "personal_ai.slack_interface.tasks.get_redis_client",
        lambda _url: fakeredis.FakeRedis(decode_responses=True),
    )

    out = submit_web_task_sync("U123", "open example.com")
    assert out == tid
    assert captured["user_id"] == "U123"
    assert captured["payload"]["goal"] == "open example.com"


def test_agent_runner_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = uuid.uuid4()
    task = SimpleNamespace(
        id=task_id,
        status=TaskStatus.PENDING,
        user_id="U1",
        cancel_requested_at=None,
        retry_count=0,
        payload={},
    )

    session = MagicMock()
    session.get.return_value = task
    session.refresh = MagicMock()

    @contextmanager
    def fake_scope():  # type: ignore[no-untyped-def]
        yield session

    monkeypatch.setattr("personal_ai.run.runner.session_scope", fake_scope)

    def transition(_tid, _from_states, to_state):  # type: ignore[no-untyped-def]
        task.status = to_state
        return task

    with patch("personal_ai.run.runner.LifecycleService") as LS:
        LS.return_value.transition.side_effect = transition
        with patch("personal_ai.run.runner.OrchestratorDispatchService") as OD:
            OD.return_value.dispatch.return_value = {}
            r = fakeredis.FakeRedis(decode_responses=True)
            q = RedisJobQueue(r)
            dlq = DeadLetterQueue(r)
            job = JobPayload(task_id=task_id, user_id="U1", type="web", payload={})
            q.enqueue(job)
            runner = AgentRunner(q, dlq, max_job_retries=3)
            runner.process_one(timeout_seconds=1)

    assert task.status == TaskStatus.COMPLETED


def test_agent_runner_dlq_after_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = uuid.uuid4()
    task = SimpleNamespace(
        id=task_id,
        status=TaskStatus.PENDING,
        user_id="U1",
        cancel_requested_at=None,
        retry_count=0,
        payload={},
    )

    session = MagicMock()
    session.get.return_value = task
    session.refresh = MagicMock()

    @contextmanager
    def fake_scope():  # type: ignore[no-untyped-def]
        yield session

    monkeypatch.setattr("personal_ai.run.runner.session_scope", fake_scope)

    def transition(_tid, _from_states, to_state):  # type: ignore[no-untyped-def]
        task.status = to_state
        return task

    with patch("personal_ai.run.runner.LifecycleService") as LS:
        LS.return_value.transition.side_effect = transition
        with patch("personal_ai.run.runner.OrchestratorDispatchService") as OD:
            OD.return_value.dispatch.side_effect = RuntimeError("fail")
            r = fakeredis.FakeRedis(decode_responses=True)
            q = RedisJobQueue(r)
            dlq = DeadLetterQueue(r)
            job = JobPayload(task_id=task_id, user_id="U1", type="web", payload={})
            q.enqueue(job)
            runner = AgentRunner(q, dlq, max_job_retries=1)
            runner.process_one(timeout_seconds=1)

    assert task.status == TaskStatus.FAILED
    rows = dlq.list_recent(limit=5)
    assert len(rows) == 1
    assert "fail" in rows[0]["last_error"]
