"""Long-running worker: dequeue, claim task, dispatch handlers, DLQ on exhaustion (T-012)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from personal_ai.config.settings import get_settings
from personal_ai.db.session import session_scope
from personal_ai.observability.logging import get_logger
from personal_ai.orchestrator.cancellation import CancellationService
from personal_ai.orchestrator.dispatch import OrchestratorDispatchService
from personal_ai.orchestrator.lifecycle import LifecycleService
from personal_ai.queue.dlq import DeadLetterQueue
from personal_ai.queue.redis_queue import RedisJobQueue
from personal_ai.queue.schemas import JobPayload
from personal_ai.run.cancel_signals import should_stop_execution
from personal_ai.run.handlers import register_default_handlers
from personal_ai.state.models import Task, TaskStatus

log = get_logger(__name__)


class AgentRunner:
    """Blocking queue consumer with lifecycle + DLQ (T-006, T-012)."""

    def __init__(
        self,
        queue: RedisJobQueue,
        dlq: DeadLetterQueue,
        *,
        max_job_retries: int | None = None,
    ) -> None:
        self._queue = queue
        self._dlq = dlq
        settings = get_settings()
        self._max_job_retries = (
            max_job_retries if max_job_retries is not None else settings.worker_max_job_retries
        )

    def process_one(self, *, timeout_seconds: float = 5.0) -> bool:
        """Dequeue and run one job. Returns False when no job was available."""
        job = self._queue.dequeue(timeout_seconds=timeout_seconds)
        if job is None:
            return False
        self._handle_job(job)
        return True

    def _handle_job(self, job: JobPayload) -> None:
        with session_scope() as session:
            task = session.get(Task, job.task_id)
            if task is None:
                log.warning("runner_orphan_job", task_id=str(job.task_id))
                return
            if task.status in (
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ):
                log.info(
                    "runner_skip_terminal_task",
                    task_id=str(job.task_id),
                    status=task.status.value,
                )
                return

            life = LifecycleService(session)
            cancel = CancellationService(session)
            orch = OrchestratorDispatchService(session, self._queue)
            register_default_handlers(orch)

            if task.status == TaskStatus.PENDING:
                life.transition(job.task_id, (TaskStatus.PENDING,), TaskStatus.RUNNING)
            elif task.status != TaskStatus.RUNNING:
                log.warning(
                    "runner_unexpected_status",
                    task_id=str(job.task_id),
                    status=task.status.value,
                )
                return

            session.refresh(task)
            if should_stop_execution(task):
                cancel.acknowledge_cancellation(job.task_id)
                return

            try:
                result = orch.dispatch(job)
            except Exception as exc:  # noqa: BLE001
                log.exception("runner_dispatch_failed", task_id=str(job.task_id), error=str(exc))
                self._fail_or_requeue(session, job, task, life, str(exc))
                return

            if isinstance(result, dict) and "payload_patch" in result:
                patch = result.get("payload_patch")
                if isinstance(patch, dict):
                    task.payload = patch

            session.refresh(task)
            if task.status == TaskStatus.RUNNING:
                life.transition(job.task_id, (TaskStatus.RUNNING,), TaskStatus.COMPLETED)
                log.info("runner_job_ok", task_id=str(job.task_id), type=job.type)
            elif task.status == TaskStatus.FAILED:
                log.info(
                    "runner_dispatch_left_failed",
                    task_id=str(job.task_id),
                    type=job.type,
                )
            elif task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                log.info(
                    "runner_job_terminal_after_dispatch",
                    task_id=str(job.task_id),
                    status=task.status.value,
                )
            else:
                log.warning(
                    "runner_unexpected_post_dispatch_status",
                    task_id=str(job.task_id),
                    status=task.status.value,
                )

    def _fail_or_requeue(
        self,
        session: Session,
        job: JobPayload,
        task: Task,
        life: LifecycleService,
        err: str,
    ) -> None:
        session.refresh(task)
        if task.status == TaskStatus.FAILED:
            log.info("runner_skip_fail_already_terminal", task_id=str(job.task_id))
            return

        next_retries = job.retries + 1
        task.retry_count = next_retries
        session.flush()

        if next_retries >= self._max_job_retries:
            self._dlq.push(task_id=job.task_id, last_error=err, job=job)
            life.transition(job.task_id, (TaskStatus.RUNNING,), TaskStatus.FAILED)
            log.warning(
                "runner_job_dlq",
                task_id=str(job.task_id),
                retries=next_retries,
                error=err,
            )
            return

        follow = JobPayload(
            task_id=job.task_id,
            user_id=job.user_id,
            type=job.type,
            payload=job.payload,
            priority=job.priority,
            retries=next_retries,
        )
        self._queue.enqueue(follow)
        log.warning(
            "runner_job_requeued",
            task_id=str(job.task_id),
            retries=next_retries,
            error=err,
        )


def run_worker_loop(*, dequeue_timeout: float = 5.0) -> None:
    """Process jobs forever (SIGINT/SIGTERM handled by process supervisor in prod)."""
    settings = get_settings()
    from personal_ai.queue.redis_queue import get_redis_client

    r = get_redis_client(settings.redis_url)
    q = RedisJobQueue(r)
    dlq = DeadLetterQueue(r)
    runner = AgentRunner(q, dlq)
    while True:
        runner.process_one(timeout_seconds=dequeue_timeout)


def drain_one_for_tests(runner: AgentRunner, *, timeout_seconds: float = 1.0) -> bool:
    """Test helper: single dequeue attempt."""
    return runner.process_one(timeout_seconds=timeout_seconds)


if __name__ == "__main__":
    run_worker_loop()
