from __future__ import annotations

import uuid
from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_ai.observability.logging import get_logger
from personal_ai.state.models import Task, TaskStatus

log = get_logger(__name__)

ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.WAITING_FOR_APPROVAL,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.WAITING_FOR_APPROVAL: frozenset(
        {
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}


def transition_allowed(current: TaskStatus, target: TaskStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


class LifecycleError(Exception):
    """Illegal lifecycle operation (T-008)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class LifecycleService:
    """Valid task state transitions with row lock (T-008)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def transition(
        self,
        task_id: uuid.UUID,
        from_states: Collection[TaskStatus],
        to_state: TaskStatus,
    ) -> Task:
        stmt = select(Task).where(Task.id == task_id).with_for_update()
        task = self._session.scalar(stmt)
        if task is None:
            raise LifecycleError("NOT_FOUND", f"Task not found: {task_id}")
        if task.status not in from_states:
            raise LifecycleError(
                "STATE_MISMATCH",
                f"Task {task_id} is {task.status.value}, expected one of "
                f"{[s.value for s in from_states]}",
            )
        if not transition_allowed(task.status, to_state):
            raise LifecycleError(
                "ILLEGAL_TRANSITION",
                f"Cannot go from {task.status.value} to {to_state.value}",
            )
        previous = task.status
        task.status = to_state
        self._session.flush()
        log.info(
            "task_lifecycle_transition",
            task_id=str(task_id),
            user_id=task.user_id,
            from_state=previous.value,
            to_state=to_state.value,
        )
        return task
