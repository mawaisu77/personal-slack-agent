"""Cooperative cancellation checks for the agent runner (T-009)."""

from __future__ import annotations

from personal_ai.state.models import Task, TaskStatus


def should_stop_execution(task: Task) -> bool:
    """True when the runner should exit the loop between iterations."""
    if task.status == TaskStatus.CANCELLED:
        return True
    return task.cancel_requested_at is not None
