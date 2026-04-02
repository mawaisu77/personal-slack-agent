from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_ai.observability.logging import get_logger
from personal_ai.orchestrator.lifecycle import LifecycleError, LifecycleService
from personal_ai.state.models import Task, TaskStatus

log = get_logger(__name__)


class CancellationService:
    """User/system cancel: flag + lifecycle (T-009)."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._lifecycle = LifecycleService(session)

    def request_cancel(self, task_id: uuid.UUID) -> Task:
        """
        Set ``cancel_requested_at``. If task is still ``pending``, move to ``cancelled``
        immediately (no worker). Otherwise the runner must acknowledge via
        ``acknowledge_cancellation`` when safe.
        """
        stmt = select(Task).where(Task.id == task_id).with_for_update()
        task = self._session.scalar(stmt)
        if task is None:
            raise LifecycleError("NOT_FOUND", f"Task not found: {task_id}")
        if task.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ):
            raise LifecycleError(
                "INVALID_STATE",
                f"Task {task_id} is already terminal: {task.status}",
            )

        now = datetime.now(tz=UTC)
        task.cancel_requested_at = now
        self._session.flush()

        log.info(
            "task_cancel_requested",
            task_id=str(task_id),
            user_id=task.user_id,
            status=task.status.value,
        )

        if task.status == TaskStatus.PENDING:
            self._lifecycle.transition(
                task_id,
                (TaskStatus.PENDING,),
                TaskStatus.CANCELLED,
            )
            task.cancellation_reason = task.cancellation_reason or "cancelled_before_start"

        return task

    def acknowledge_cancellation(self, task_id: uuid.UUID) -> Task:
        """Worker cooperatively finishes: transition active task to ``cancelled``."""
        stmt = select(Task).where(Task.id == task_id).with_for_update()
        task = self._session.scalar(stmt)
        if task is None:
            raise LifecycleError("NOT_FOUND", f"Task not found: {task_id}")
        if task.cancel_requested_at is None:
            raise LifecycleError("NO_CANCEL_REQUEST", f"No cancel request for {task_id}")
        if task.status == TaskStatus.CANCELLED:
            return task
        if task.status not in (TaskStatus.RUNNING, TaskStatus.WAITING_FOR_APPROVAL):
            raise LifecycleError(
                "INVALID_STATE",
                f"Cannot ack cancel from state {task.status.value}",
            )
        self._lifecycle.transition(
            task_id,
            (TaskStatus.RUNNING, TaskStatus.WAITING_FOR_APPROVAL),
            TaskStatus.CANCELLED,
        )
        task.cancellation_reason = task.cancellation_reason or "cancelled_by_user"
        return task
