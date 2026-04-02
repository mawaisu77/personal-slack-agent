from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from personal_ai.state.models import Checkpoint


class CheckpointStore:
    """Append and read checkpoints for task resume (T-002)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append_checkpoint(self, task_id: uuid.UUID, payload: dict[str, Any]) -> Checkpoint:
        """Append the next sequence row for this task (idempotent per distinct sequence)."""
        subq = select(func.coalesce(func.max(Checkpoint.sequence), 0)).where(
            Checkpoint.task_id == task_id
        )
        next_seq = 1 + self._session.scalar(subq)
        row = Checkpoint(
            id=uuid.uuid4(),
            task_id=task_id,
            sequence=next_seq,
            payload_json=payload,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def latest_checkpoint(self, task_id: uuid.UUID) -> Checkpoint | None:
        """Highest sequence checkpoint for resume."""
        stmt = (
            select(Checkpoint)
            .where(Checkpoint.task_id == task_id)
            .order_by(Checkpoint.sequence.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)
