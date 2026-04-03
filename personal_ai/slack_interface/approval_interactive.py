"""Slack Block Kit approve/reject for human-in-the-loop (T-039)."""

from __future__ import annotations

import uuid

from slack_bolt.async_app import AsyncApp

from personal_ai.approvals.audit import ApprovalAuditStore
from personal_ai.approvals.store import ApprovalStore
from personal_ai.db.session import session_scope
from personal_ai.observability.logging import get_logger
from personal_ai.state.models import ApprovalStatus

log = get_logger(__name__)


def register_approval_handlers(slack_app: AsyncApp) -> None:
    @slack_app.action("approval_decision")
    async def _on_decision(ack, body):  # type: ignore[no-untyped-def]
        await ack()
        try:
            user_id = body["user"]["id"]
            val = body["actions"][0]["value"]
            aid_str, decision = val.split("|", 1)
            approval_id = uuid.UUID(aid_str)
        except (KeyError, ValueError) as exc:
            log.warning("approval_action_parse_failed", error=str(exc))
            return

        status = ApprovalStatus.APPROVED if decision == "approve" else ApprovalStatus.REJECTED
        with session_scope() as session:
            store = ApprovalStore(session)
            try:
                store.update_status(approval_id, status)
            except KeyError:
                log.warning("approval_not_found", approval_id=str(approval_id))
                return
            audit = ApprovalAuditStore(session)
            audit.append(
                approval_id=approval_id,
                actor=user_id,
                decision=status.value,
                notes=None,
            )
