from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from personal_ai.observability.logging import get_logger
from personal_ai.orchestrator.budget import BudgetService
from personal_ai.orchestrator.voice_routing import is_voice_job
from personal_ai.queue.redis_queue import RedisJobQueue
from personal_ai.queue.schemas import JobPayload
from personal_ai.state.models import Task, TaskStatus, TaskType

log = get_logger(__name__)

TaskHandler = Callable[[JobPayload], dict[str, Any]]


class OrchestratorDispatchService:
    """Submit tasks and dispatch queued jobs by type (T-007)."""

    def __init__(self, session: Session, queue: RedisJobQueue) -> None:
        self._session = session
        self._queue = queue
        self._handlers: dict[str, TaskHandler] = {}

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        self._handlers[task_type] = handler

    def submit_task(
        self,
        *,
        user_id: str,
        task_type: TaskType,
        payload: dict[str, Any],
        priority: int = 0,
    ) -> Task:
        BudgetService(self._session).enforce_user_limits(user_id)
        task = Task(
            id=uuid.uuid4(),
            user_id=user_id,
            type=task_type,
            status=TaskStatus.PENDING,
            payload=payload,
            retry_count=0,
        )
        self._session.add(task)
        self._session.flush()
        job = JobPayload(
            task_id=task.id,
            user_id=user_id,
            type=task_type.value,
            payload=payload,
            priority=priority,
            retries=0,
        )
        self._queue.enqueue(job)
        return task

    def dispatch(self, job: JobPayload) -> dict[str, Any]:
        if is_voice_job(job):
            log.info(
                "orchestrator_voice_route",
                task_id=str(job.task_id),
                user_id=job.user_id,
            )
        handler = self._handlers.get(job.type)
        if handler is None:
            raise KeyError(f"No handler registered for type={job.type}")
        return handler(job)
