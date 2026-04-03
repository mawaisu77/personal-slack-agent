from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from personal_ai.db.base import Base


class ApprovalAudit(Base):
    """Append-only approval decisions for compliance (T-046)."""

    __tablename__ = "approval_audit"
    __table_args__ = (
        Index("ix_approval_audit_approval_id", "approval_id"),
        Index("ix_approval_audit_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approvals.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ApprovalAuditStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        *,
        approval_id: uuid.UUID,
        actor: str,
        decision: str,
        notes: str | None = None,
    ) -> ApprovalAudit:
        row = ApprovalAudit(
            approval_id=approval_id,
            actor=actor,
            decision=decision,
            notes=notes,
        )
        self._session.add(row)
        self._session.flush()
        return row
