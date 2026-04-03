"""Read-only task lookups scoped by Slack user (T-035)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_ai.state.models import Task


def get_task_owned(session: Session, task_id: uuid.UUID, user_id: str) -> Task | None:
    task = session.get(Task, task_id)
    if task is None or task.user_id != user_id:
        return None
    return task


def list_tasks_for_user(session: Session, user_id: str, *, limit: int = 20) -> Sequence[Task]:
    stmt = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    return session.scalars(stmt).all()
