"""In-memory execution state with checkpoint persistence (T-013)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from personal_ai.state.models import Checkpoint, Task


@dataclass
class ExecutionState:
    """Per-run agent loop state (mirrored into ``checkpoints.payload_json``)."""

    run_id: str
    step_index: int = 0
    data: dict[str, Any] = field(default_factory=dict)


class ExecutionStateStore:
    """
    In-memory dict keyed by ``run_id``; flush to ``checkpoints`` for resume (T-002, T-013).
    """

    def __init__(self) -> None:
        self._by_run: dict[str, ExecutionState] = {}

    def get(self, run_id: str) -> ExecutionState | None:
        return self._by_run.get(run_id)

    def get_or_create(self, run_id: str) -> ExecutionState:
        if run_id not in self._by_run:
            self._by_run[run_id] = ExecutionState(run_id=run_id)
        return self._by_run[run_id]

    def put(self, state: ExecutionState) -> None:
        self._by_run[state.run_id] = state

    def merge_from_payload(self, run_id: str, payload: dict[str, Any]) -> ExecutionState:
        """Apply checkpoint JSON (e.g. after worker restart)."""
        st = ExecutionState(
            run_id=payload.get("run_id", run_id),
            step_index=int(payload.get("step_index", 0)),
            data=dict(payload.get("data", {})),
        )
        self.put(st)
        return st


def next_checkpoint_sequence(session: Session, task_id: uuid.UUID) -> int:
    stmt = select(func.coalesce(func.max(Checkpoint.sequence), 0)).where(
        Checkpoint.task_id == task_id,
    )
    m = session.scalar(stmt)
    return int(m) + 1


def flush_execution_checkpoint(
    session: Session,
    *,
    task_id: uuid.UUID,
    state: ExecutionState,
) -> Checkpoint:
    """Persist current in-memory state as a new checkpoint row."""
    if session.get(Task, task_id) is None:
        raise ValueError(f"Unknown task_id={task_id}")

    seq = next_checkpoint_sequence(session, task_id)
    payload_json: dict[str, Any] = {
        "run_id": state.run_id,
        "step_index": state.step_index,
        "data": state.data,
    }
    row = Checkpoint(
        task_id=task_id,
        sequence=seq,
        payload_json=payload_json,
    )
    session.add(row)
    session.flush()
    return row


def load_latest_execution_payload(session: Session, task_id: uuid.UUID) -> dict[str, Any] | None:
    """Latest checkpoint blob for a task (for resume / merge tests)."""
    stmt = (
        select(Checkpoint)
        .where(Checkpoint.task_id == task_id)
        .order_by(Checkpoint.sequence.desc())
        .limit(1)
    )
    row = session.scalar(stmt)
    if row is None:
        return None
    return dict(row.payload_json)


def hydrate_store_from_latest_checkpoint(
    store: ExecutionStateStore,
    session: Session,
    task_id: uuid.UUID,
    *,
    run_id: str,
) -> ExecutionState | None:
    """Load latest DB checkpoint into the in-memory store."""
    payload = load_latest_execution_payload(session, task_id)
    if payload is None:
        return None
    return store.merge_from_payload(run_id, payload)


def maybe_flush_periodic(
    session: Session,
    *,
    task_id: uuid.UUID,
    store: ExecutionStateStore,
    run_id: str,
    every_n_steps: int,
) -> bool:
    """
    Flush when ``step_index`` is a positive multiple of ``every_n_steps``.
    Use from the agent loop for periodic durability without writing every step.
    """
    st = store.get(run_id)
    if st is None or every_n_steps < 1:
        return False
    if st.step_index <= 0 or st.step_index % every_n_steps != 0:
        return False
    flush_execution_checkpoint(session, task_id=task_id, state=st)
    return True
