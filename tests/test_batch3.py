from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from personal_ai.approvals.store import ApprovalStore
from personal_ai.observability.ai_logging import log_ai_io, redact_text
from personal_ai.observability.context import task_context
from personal_ai.observability.logging import configure_logging
from personal_ai.orchestrator.cancellation import CancellationService
from personal_ai.queue.redis_queue import RedisJobQueue
from personal_ai.queue.schemas import JobPayload
from personal_ai.run.cancel_signals import should_stop_execution
from personal_ai.state.models import Task, TaskStatus
from personal_ai.voice.factory import get_voice_provider
from personal_ai.voice.provider import NoopVoiceProvider
from personal_ai.web.session_manager import PlaywrightSessionManager


def _job(priority: int, suffix: str) -> JobPayload:
    return JobPayload(
        task_id=uuid.uuid4(),
        user_id="U1",
        type="web",
        payload={"n": suffix},
        priority=priority,
    )


def test_redis_queue_higher_priority_dequeues_first() -> None:
    r = fakeredis.FakeRedis(decode_responses=True)
    q = RedisJobQueue(r)
    low = _job(0, "low")
    high = _job(50, "high")
    q.enqueue(low)
    q.enqueue(high)
    first = q.dequeue(timeout_seconds=1)
    second = q.dequeue(timeout_seconds=1)
    assert first is not None and second is not None
    assert first.priority == 50
    assert second.priority == 0


def test_redis_queue_empty_returns_none() -> None:
    r = fakeredis.FakeRedis(decode_responses=True)
    q = RedisJobQueue(r)
    # timeout 0 = block forever on real Redis; use small positive timeout for tests.
    assert q.dequeue(timeout_seconds=1) is None


def test_should_stop_execution() -> None:
    t = MagicMock(spec=Task)
    t.status = TaskStatus.RUNNING
    t.cancel_requested_at = None
    assert should_stop_execution(t) is False
    t.cancel_requested_at = datetime.now(tz=UTC)
    assert should_stop_execution(t) is True
    t.cancel_requested_at = None
    t.status = TaskStatus.CANCELLED
    assert should_stop_execution(t) is True


def test_cancellation_pending_immediate_cancel() -> None:
    tid = uuid.uuid4()
    task = MagicMock(spec=Task)
    task.id = tid
    task.status = TaskStatus.PENDING
    task.user_id = "U"
    task.cancellation_reason = None
    session = MagicMock()
    session.scalar.return_value = task

    life = MagicMock()
    with patch("personal_ai.orchestrator.cancellation.LifecycleService", return_value=life):
        svc = CancellationService(session)
        out = svc.request_cancel(tid)

    assert out is task
    assert task.cancel_requested_at is not None
    life.transition.assert_called_once()
    assert life.transition.call_args[0][2] == TaskStatus.CANCELLED


def test_cancellation_running_sets_flag_only() -> None:
    tid = uuid.uuid4()
    task = MagicMock(spec=Task)
    task.id = tid
    task.status = TaskStatus.RUNNING
    task.user_id = "U"
    session = MagicMock()
    session.scalar.return_value = task

    life = MagicMock()
    with patch("personal_ai.orchestrator.cancellation.LifecycleService", return_value=life):
        svc = CancellationService(session)
        svc.request_cancel(tid)

    assert task.cancel_requested_at is not None
    life.transition.assert_not_called()


def test_voice_factory_noop() -> None:
    p = get_voice_provider()
    assert isinstance(p, NoopVoiceProvider)
    cid = p.start_call("+15551234567")
    assert cid.startswith("noop-")


def test_approval_store_create_calls_add() -> None:
    session = MagicMock()
    store = ApprovalStore(session)
    tid = uuid.uuid4()
    exp = datetime(2030, 1, 1, tzinfo=UTC)
    store.create(
        task_id=tid,
        action_summary="Pay $100",
        screenshot_url="https://example.com/s.png",
        expires_at=exp,
    )
    session.add.assert_called_once()


def test_redact_text_masks_secret() -> None:
    s = 'token: "sk-live-xxxxx" and ok'
    assert "[REDACTED]" in redact_text(s)


def test_log_ai_io_with_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(json_logs=True)
    try:
        with task_context("t-1", "U9"):
            log_ai_io(model="claude", prompt="hi", completion="bye")
        out = capsys.readouterr().out
        assert "t-1" in out
    finally:
        configure_logging(json_logs=False)


@patch("playwright.sync_api.sync_playwright")
def test_playwright_session_manager_context_per_task(mock_sync: MagicMock) -> None:
    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_ctx = MagicMock()
    mock_browser.new_context.return_value = mock_ctx
    mock_pw.chromium.launch.return_value = mock_browser
    mock_sync.return_value.start.return_value = mock_pw

    m = PlaywrightSessionManager(user_data_dir="/tmp/pw-test-profile")
    m.start()
    c1 = m.new_context_for_task("task-a")
    c2 = m.new_context_for_task("task-b")
    assert c1 is mock_ctx
    assert c2 is mock_ctx
    assert mock_browser.new_context.call_count == 2
    m.shutdown()
