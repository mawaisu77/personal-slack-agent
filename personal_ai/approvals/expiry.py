"""Expire pending approvals past ``expires_at`` (T-041)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_ai.approvals.audit import ApprovalAuditStore
from personal_ai.approvals.store import ApprovalStore
from personal_ai.observability.logging import get_logger
from personal_ai.state.models import Approval, ApprovalStatus

log = get_logger(__name__)


def expire_overdue_approvals(session: Session) -> int:
    """
    Mark overdue pending approvals as rejected; workers polling those rows exit as reject (T-041).

    Does not force task status here: the blocked worker observes ``REJECTED`` and fails the task.
    """
    now = datetime.now(tz=UTC)
    stmt = select(Approval).where(
        Approval.status == ApprovalStatus.PENDING,
        Approval.expires_at < now,
    )
    rows = list(session.scalars(stmt).all())
    if not rows:
        return 0

    store = ApprovalStore(session)
    audit = ApprovalAuditStore(session)
    for row in rows:
        store.update_status(row.id, ApprovalStatus.REJECTED)
        audit.append(
            approval_id=row.id,
            actor="system",
            decision="expired",
            notes="approval_timeout",
        )
        log.info("approval_expired", approval_id=str(row.id), task_id=str(row.task_id))
    session.flush()
    return len(rows)
