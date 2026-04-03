"""Human approval gate for irreversible browser actions (T-038)."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.orm import Session

from personal_ai.approvals.store import ApprovalStore
from personal_ai.config.secrets import get_secret
from personal_ai.config.settings import get_settings
from personal_ai.observability.logging import get_logger
from personal_ai.orchestrator.lifecycle import LifecycleService
from personal_ai.state.models import Approval, ApprovalStatus, TaskStatus
from personal_ai.web.screenshot_storage import LocalScreenshotStorage

log = get_logger(__name__)


class ApprovalWorkflow:
    """
    Moves task to ``waiting_for_approval``, posts Slack, blocks until approve/reject (T-038).

    Resolution is observed via DB polling so the Slack interaction handler can run in the
    gateway process (T-039).
    """

    def __init__(
        self,
        session: Session,
        *,
        task_id: uuid.UUID,
        user_id: str,
        slack_channel_id: str,
    ) -> None:
        self._session = session
        self._task_id = task_id
        self._user_id = user_id
        self._channel_id = slack_channel_id
        settings = get_settings()
        self._poll_interval = settings.approval_poll_interval_sec
        self._timeout = settings.approval_wait_timeout_sec

    def request_approval_for_action(
        self,
        *,
        action: dict[str, Any],
        capture: dict[str, Any],
    ) -> bool:
        """
        Returns ``True`` if approved, ``False`` if rejected. Raises on timeout / missing row.
        """
        life = LifecycleService(self._session)
        life.transition(
            self._task_id,
            (TaskStatus.RUNNING,),
            TaskStatus.WAITING_FOR_APPROVAL,
        )

        act = action.get("action", "")
        tgt = str(action.get("target", ""))[:200]
        rsn = str(action.get("reason", ""))[:200]
        summary = f"{act} {tgt} — {rsn}"
        png = capture.get("screenshot_png") if isinstance(capture, dict) else None
        screenshot_url: str | None = None
        if isinstance(png, (bytes, bytearray)) and len(png) > 100:
            settings = get_settings()
            store = LocalScreenshotStorage(
                settings.screenshot_storage_dir,
                public_base_url=settings.public_assets_base_url,
            )
            screenshot_url = store.store_png(
                task_id=str(self._task_id),
                name="approval",
                data=bytes(png),
            )

        exp = datetime.now(tz=UTC) + timedelta(hours=24)
        a_store = ApprovalStore(self._session)
        row = a_store.create(
            task_id=self._task_id,
            action_summary=summary[:2000],
            screenshot_url=screenshot_url,
            expires_at=exp,
            status=ApprovalStatus.PENDING,
        )
        self._session.commit()

        self._post_slack_approval(row.id, summary)

        status = self._poll_until_terminal(row.id)
        if status == ApprovalStatus.APPROVED:
            life.transition(
                self._task_id,
                (TaskStatus.WAITING_FOR_APPROVAL,),
                TaskStatus.RUNNING,
            )
            self._session.commit()
            return True
        if status == ApprovalStatus.REJECTED:
            life.transition(
                self._task_id,
                (TaskStatus.WAITING_FOR_APPROVAL,),
                TaskStatus.FAILED,
            )
            self._session.commit()
            return False
        msg = f"unexpected approval status {status}"
        raise RuntimeError(msg)

    def _post_slack_approval(self, approval_id: uuid.UUID, summary: str) -> None:
        token = get_secret("SLACK_BOT_TOKEN")
        client = WebClient(token=token)
        blocks: list[dict[str, Any]] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Approval required*\n{summary[:2500]}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": "approval_decision",
                        "value": f"{approval_id}|approve",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": "approval_decision",
                        "value": f"{approval_id}|reject",
                    },
                ],
            },
        ]
        try:
            client.chat_postEphemeral(
                channel=self._channel_id,
                user=self._user_id,
                blocks=blocks,
                text=f"Approval required: {summary[:200]}",
            )
        except SlackApiError as exc:
            log.warning("approval_slack_post_failed", error=str(exc))

    def _poll_until_terminal(self, approval_id: uuid.UUID) -> ApprovalStatus:
        t0 = time.monotonic()
        while True:
            row = self._session.get(Approval, approval_id)
            if row is None:
                msg = f"approval row missing: {approval_id}"
                raise RuntimeError(msg)
            self._session.refresh(row)
            if row.status != ApprovalStatus.PENDING:
                return row.status
            if time.monotonic() - t0 > self._timeout:
                log.warning("approval_wait_timeout", approval_id=str(approval_id))
                life = LifecycleService(self._session)
                life.transition(
                    self._task_id,
                    (TaskStatus.WAITING_FOR_APPROVAL,),
                    TaskStatus.FAILED,
                )
                self._session.commit()
                raise TimeoutError("approval_wait_timeout")
            time.sleep(self._poll_interval)
            self._session.commit()
