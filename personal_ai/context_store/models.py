from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from personal_ai.db.base import Base


class UserContext(Base):
    """Structured user profile fragments (T-042)."""

    __tablename__ = "user_context"
    __table_args__ = (Index("ix_user_context_user_key", "user_id", "context_key", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    context_key: Mapped[str] = mapped_column(String(128), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    encryption_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
