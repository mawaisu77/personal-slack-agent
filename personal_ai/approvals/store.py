from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_ai.state.models import Approval, ApprovalStatus


class ApprovalStore:
    """CRUD for approval objects (T-037)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        task_id: uuid.UUID,
        action_summary: str,
        screenshot_url: str | None,
        expires_at: datetime,
        status: ApprovalStatus = ApprovalStatus.PENDING,
    ) -> Approval:
        row = Approval(
            id=uuid.uuid4(),
            task_id=task_id,
            action_summary=action_summary,
            screenshot_url=screenshot_url,
            status=status,
            expires_at=expires_at,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get(self, approval_id: uuid.UUID) -> Approval | None:
        return self._session.get(Approval, approval_id)

    def update_status(self, approval_id: uuid.UUID, status: ApprovalStatus) -> Approval:
        row = self.get(approval_id)
        if row is None:
            msg = f"Approval not found: {approval_id}"
            raise KeyError(msg)
        row.status = status
        self._session.flush()
        return row

    def list_for_task(self, task_id: uuid.UUID) -> list[Approval]:
        stmt = (
            select(Approval)
            .where(Approval.task_id == task_id)
            .order_by(Approval.created_at.desc())
        )
        return list(self._session.scalars(stmt).all())
