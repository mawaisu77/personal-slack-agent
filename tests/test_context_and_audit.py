from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from personal_ai.approvals.audit import ApprovalAuditStore
from personal_ai.context_store.store import ContextStore


def test_context_store_upsert_adds_when_missing() -> None:
    session = MagicMock()
    session.scalar.return_value = None
    store = ContextStore(session)
    row = store.upsert(user_id="U1", context_key="profile", value_json={"name": "Ada"})
    assert row.context_key == "profile"
    session.add.assert_called_once()


def test_context_store_upsert_updates_existing() -> None:
    session = MagicMock()
    existing = MagicMock()
    existing.value_json = {"name": "old"}
    session.scalar.return_value = existing
    store = ContextStore(session)
    out = store.upsert(user_id="U1", context_key="profile", value_json={"name": "new"})
    assert out is existing
    assert existing.value_json == {"name": "new"}


def test_approval_audit_append() -> None:
    session = MagicMock()
    store = ApprovalAuditStore(session)
    aid = uuid.uuid4()
    row = store.append(approval_id=aid, actor="U123", decision="approved", notes="ok")
    assert row.approval_id == aid
    session.add.assert_called_once()
