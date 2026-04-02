"""T-047 — exhaustive lifecycle transition matrix + service behavior (mocked DB)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from personal_ai.orchestrator.lifecycle import (
    ALLOWED_TRANSITIONS,
    LifecycleError,
    LifecycleService,
    transition_allowed,
)
from personal_ai.state.models import TaskStatus


def test_transition_matrix_exhaustive() -> None:
    for src in TaskStatus:
        for dst in TaskStatus:
            expected = dst in ALLOWED_TRANSITIONS[src]
            assert transition_allowed(src, dst) is expected, f"{src!r} -> {dst!r}"


@pytest.mark.parametrize(
    ("from_s", "to_s"),
    [
        (TaskStatus.PENDING, TaskStatus.RUNNING),
        (TaskStatus.PENDING, TaskStatus.CANCELLED),
        (TaskStatus.RUNNING, TaskStatus.WAITING_FOR_APPROVAL),
        (TaskStatus.RUNNING, TaskStatus.COMPLETED),
        (TaskStatus.RUNNING, TaskStatus.FAILED),
        (TaskStatus.RUNNING, TaskStatus.CANCELLED),
        (TaskStatus.WAITING_FOR_APPROVAL, TaskStatus.RUNNING),
        (TaskStatus.WAITING_FOR_APPROVAL, TaskStatus.COMPLETED),
        (TaskStatus.WAITING_FOR_APPROVAL, TaskStatus.FAILED),
        (TaskStatus.WAITING_FOR_APPROVAL, TaskStatus.CANCELLED),
    ],
)
@patch("personal_ai.orchestrator.lifecycle.log")
def test_lifecycle_service_allowed_edge(
    _mock_log: MagicMock,
    from_s: TaskStatus,
    to_s: TaskStatus,
) -> None:
    tid = uuid.uuid4()

    class _Task:
        __tablename__ = "tasks"

    task = _Task()
    task.id = tid
    task.status = from_s
    task.user_id = "U1"
    session = MagicMock()
    session.scalar.return_value = task
    svc = LifecycleService(session)
    out = svc.transition(tid, (from_s,), to_s)
    assert out.status == to_s
    session.flush.assert_called()


def test_lifecycle_service_rejects_illegal() -> None:
    tid = uuid.uuid4()

    class _T:
        pass

    task = _T()
    task.id = tid
    task.status = TaskStatus.COMPLETED
    task.user_id = "U1"
    session = MagicMock()
    session.scalar.return_value = task
    svc = LifecycleService(session)
    with pytest.raises(LifecycleError) as ei:
        svc.transition(tid, (TaskStatus.COMPLETED,), TaskStatus.RUNNING)
    assert ei.value.code == "ILLEGAL_TRANSITION"
