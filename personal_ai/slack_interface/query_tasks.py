"""Sync helpers for Slack slash queries (T-035)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from personal_ai.db.session import session_scope
from personal_ai.orchestrator.cancellation import CancellationService
from personal_ai.orchestrator.lifecycle import LifecycleError
from personal_ai.orchestrator.task_queries import get_task_owned, list_tasks_for_user


def parse_task_uuid(text: str) -> uuid.UUID | None:
    raw = (text or "").strip()
    if not raw:
        return None
    token = raw.split()[0]
    try:
        return uuid.UUID(token)
    except ValueError:
        loose = re.search(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            raw,
        )
        if loose:
            return uuid.UUID(loose.group(0))
        return None


def get_task_status_sync(user_id: str, task_id: uuid.UUID) -> dict[str, Any] | None:
    with session_scope() as session:
        task = get_task_owned(session, task_id, user_id)
        if task is None:
            return None
        return {
            "id": str(task.id),
            "status": task.status.value,
            "type": task.type.value,
            "retry_count": task.retry_count,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "cancel_requested_at": task.cancel_requested_at.isoformat()
            if task.cancel_requested_at
            else None,
        }


def cancel_task_sync(user_id: str, task_id: uuid.UUID) -> tuple[bool, str]:
    with session_scope() as session:
        task = get_task_owned(session, task_id, user_id)
        if task is None:
            return False, "not_found"
        cancel = CancellationService(session)
        try:
            cancel.request_cancel(task_id)
        except LifecycleError as exc:
            return False, exc.code
        return True, "ok"


def list_task_history_sync(user_id: str, *, limit: int = 15) -> list[dict[str, Any]]:
    cap = max(1, min(limit, 50))
    with session_scope() as session:
        rows = list_tasks_for_user(session, user_id, limit=cap)
        return [
            {
                "id": str(t.id),
                "status": t.status.value,
                "type": t.type.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in rows
        ]
