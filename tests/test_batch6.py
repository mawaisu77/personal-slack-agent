from __future__ import annotations

import uuid
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from personal_ai.orchestrator.dispatch import OrchestratorDispatchService
from personal_ai.orchestrator.task_queries import get_task_owned
from personal_ai.orchestrator.voice_routing import is_voice_job
from personal_ai.queue.redis_queue import RedisJobQueue
from personal_ai.queue.schemas import JobPayload
from personal_ai.run.execution_state import (
    ExecutionStateStore,
    flush_execution_checkpoint,
    hydrate_store_from_latest_checkpoint,
    maybe_flush_periodic,
)
from personal_ai.run.runner import AgentRunner
from personal_ai.slack_interface.query_tasks import parse_task_uuid
from personal_ai.slack_interface.tasks import submit_call_task_sync
from personal_ai.state.models import TaskStatus
from personal_ai.web.executor import execute_action_with_retry
from personal_ai.web.navigation import NavigationExpectation, validate_navigation


def test_execution_state_merge_and_flush() -> None:
    store = ExecutionStateStore()
    st = store.get_or_create("run-1")
    st.step_index = 2
    st.data["k"] = "v"

    session = MagicMock()
    tid = uuid.uuid4()
    session.get.return_value = MagicMock()
    session.scalar.return_value = 0

    flush_execution_checkpoint(session, task_id=tid, state=st)
    session.add.assert_called_once()
    added = session.add.call_args[0][0]
    assert added.sequence == 1
    assert added.payload_json["run_id"] == "run-1"
    assert added.payload_json["step_index"] == 2


def test_hydrate_store_from_checkpoint() -> None:
    store = ExecutionStateStore()
    session = MagicMock()
    tid = uuid.uuid4()
    cp = MagicMock()
    cp.payload_json = {"run_id": "run-x", "step_index": 4, "data": {"n": 1}}
    session.scalar.return_value = cp

    out = hydrate_store_from_latest_checkpoint(store, session, tid, run_id="run-x")
    assert out is not None
    assert out.step_index == 4
    assert store.get("run-x") is not None


def test_maybe_flush_periodic() -> None:
    store = ExecutionStateStore()
    st = store.get_or_create("r")
    st.step_index = 10
    session = MagicMock()
    tid = uuid.uuid4()
    session.get.return_value = MagicMock()
    session.scalar.return_value = 0

    flushed = maybe_flush_periodic(
        session,
        task_id=tid,
        store=store,
        run_id="r",
        every_n_steps=5,
    )
    assert flushed is True
    session.add.assert_called_once()


def test_execute_action_with_retry_eventually_ok() -> None:
    page = MagicMock()
    loc = MagicMock()
    page.locator.return_value = loc
    loc.first.click.side_effect = [RuntimeError("transient"), RuntimeError("transient"), None]

    r = execute_action_with_retry(
        page,
        {"action": "click", "target": "button", "confidence": 1, "reason": "r"},
        min_attempts=3,
    )
    assert r["ok"] is True
    assert loc.first.click.call_count == 3


def test_execute_action_with_retry_all_fail() -> None:
    page = MagicMock()
    loc = MagicMock()
    page.locator.return_value = loc
    loc.first.click.side_effect = RuntimeError("bad")

    with pytest.raises(RuntimeError):
        execute_action_with_retry(
            page,
            {"action": "click", "target": "button", "confidence": 1, "reason": "r"},
            min_attempts=3,
        )


def test_validate_navigation_path() -> None:
    page = MagicMock()
    page.url = "https://example.test/app/foo"
    page.title.return_value = "App"
    ok, _ = validate_navigation(page, NavigationExpectation(path_contains="/app/"))
    assert ok is True

    bad, reason = validate_navigation(page, NavigationExpectation(path_contains="/other/"))
    assert bad is False
    assert "path_missing" in reason


def test_validate_navigation_title() -> None:
    page = MagicMock()
    page.url = "https://example.test/"
    page.title.return_value = "Welcome"
    ok, _ = validate_navigation(page, NavigationExpectation(title_contains="Welcome"))
    assert ok is True


def test_is_voice_job() -> None:
    j = JobPayload(
        task_id=uuid.uuid4(),
        user_id="U",
        type="call",
        payload={},
    )
    assert is_voice_job(j) is True
    j2 = JobPayload(task_id=j.task_id, user_id="U", type="web", payload={})
    assert is_voice_job(j2) is False


def test_get_task_owned_filters_user() -> None:
    session = MagicMock()
    tid = uuid.uuid4()
    task = MagicMock()
    task.user_id = "other"
    session.get.return_value = task
    assert get_task_owned(session, tid, "me") is None


def test_parse_task_uuid() -> None:
    u = uuid.uuid4()
    assert parse_task_uuid(f"  {u}  ") == u
    assert parse_task_uuid(f"see {u} end") == u
    assert parse_task_uuid("") is None


def test_submit_call_task_sync(monkeypatch: pytest.MonkeyPatch) -> None:
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

    out = submit_call_task_sync("U9", "+1 555 555 0199")
    assert out == tid
    assert captured["task_type"].value == "call"


def test_call_job_completes_via_voice_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    task_id = uuid.uuid4()
    task = SimpleNamespace(
        id=task_id,
        status=TaskStatus.PENDING,
        user_id="U1",
        cancel_requested_at=None,
        retry_count=0,
        payload={"phone": "+15555550123"},
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

    fake_provider = MagicMock()
    fake_provider.start_call.return_value = "call-test-id"

    with patch("personal_ai.run.runner.LifecycleService") as LS:
        LS.return_value.transition.side_effect = transition
        with patch("personal_ai.run.handlers.get_voice_provider", return_value=fake_provider):
            r = fakeredis.FakeRedis(decode_responses=True)
            q = RedisJobQueue(r)
            from personal_ai.queue.dlq import DeadLetterQueue

            dlq = DeadLetterQueue(r)
            job = JobPayload(
                task_id=task_id,
                user_id="U1",
                type="call",
                payload={"phone": "+15555550123"},
            )
            q.enqueue(job)
            runner = AgentRunner(q, dlq, max_job_retries=3)
            runner.process_one(timeout_seconds=1)

    assert task.status == TaskStatus.COMPLETED
    fake_provider.start_call.assert_called_once()


def test_dispatch_logs_voice_route() -> None:
    job = JobPayload(task_id=uuid.uuid4(), user_id="Ux", type="call", payload={})
    session = MagicMock()
    q = MagicMock()
    orch = OrchestratorDispatchService(session, q)
    orch.register_handler("call", lambda j: {"ok": True})
    with patch("personal_ai.orchestrator.dispatch.log") as log:
        orch.dispatch(job)
        log.info.assert_any_call(
            "orchestrator_voice_route",
            task_id=str(job.task_id),
            user_id="Ux",
        )
