"""Per-user submission and concurrency limits (T-054, T-057)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from personal_ai.config.settings import get_settings
from personal_ai.observability.logging import get_logger
from personal_ai.state.models import Task, TaskStatus

log = get_logger(__name__)


class BudgetExceededError(Exception):
    """Raised when a user exceeds configured task budgets."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class BudgetService:
    """Enforce caps before enqueue (T-054, T-057)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def enforce_user_limits(self, user_id: str) -> None:
        settings = get_settings()
        concurrent_cap = settings.max_concurrent_tasks_per_user
        daily_cap = settings.max_daily_tasks_per_user

        if concurrent_cap > 0:
            n = self._count_active_tasks(user_id)
            if n >= concurrent_cap:
                msg = f"Concurrent task limit reached ({concurrent_cap} active tasks)."
                raise BudgetExceededError("CONCURRENT_CAP", msg)

        if daily_cap > 0:
            n = self._count_tasks_since_midnight_utc(user_id)
            if n >= daily_cap:
                msg = f"Daily task submission limit reached ({daily_cap} per UTC day)."
                raise BudgetExceededError("DAILY_CAP", msg)

        log.debug("budget_ok", user_id=user_id)

    def _count_active_tasks(self, user_id: str) -> int:
        stmt = select(func.count()).select_from(Task).where(
            Task.user_id == user_id,
            Task.status.in_(
                (
                    TaskStatus.PENDING,
                    TaskStatus.RUNNING,
                    TaskStatus.WAITING_FOR_APPROVAL,
                ),
            ),
        )
        return int(self._session.scalar(stmt) or 0)

    def _count_tasks_since_midnight_utc(self, user_id: str) -> int:
        now = datetime.now(tz=UTC)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count()).select_from(Task).where(
            Task.user_id == user_id,
            Task.created_at >= start,
        )
        return int(self._session.scalar(stmt) or 0)
