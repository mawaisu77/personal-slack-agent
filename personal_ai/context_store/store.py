from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from personal_ai.context_store.models import UserContext


class ContextStore:
    """Minimal CRUD for context fields (T-042)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(
        self,
        *,
        user_id: str,
        context_key: str,
        value_json: dict,
        encryption_version: str = "v1",
    ) -> UserContext:
        stmt = select(UserContext).where(
            UserContext.user_id == user_id,
            UserContext.context_key == context_key,
        )
        row = self._session.scalar(stmt)
        if row is None:
            row = UserContext(
                user_id=user_id,
                context_key=context_key,
                value_json=value_json,
                encryption_version=encryption_version,
            )
            self._session.add(row)
        else:
            row.value_json = value_json
            row.encryption_version = encryption_version
        self._session.flush()
        return row

    def get(self, *, user_id: str, context_key: str) -> UserContext | None:
        stmt = select(UserContext).where(
            UserContext.user_id == user_id,
            UserContext.context_key == context_key,
        )
        return self._session.scalar(stmt)
