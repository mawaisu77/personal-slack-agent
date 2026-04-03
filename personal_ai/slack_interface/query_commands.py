"""Register `/status`, `/cancel`, `/history` (T-035)."""

from __future__ import annotations

import asyncio
from functools import partial

from slack_bolt.async_app import AsyncApp

from personal_ai.observability.logging import get_logger
from personal_ai.slack_interface.query_tasks import (
    cancel_task_sync,
    get_task_status_sync,
    list_task_history_sync,
    parse_task_uuid,
)

log = get_logger(__name__)


def register_query_commands(slack_app: AsyncApp) -> None:
    @slack_app.command("/status")
    async def _status(ack, command, client):  # type: ignore[no-untyped-def]
        await ack({"text": "Looking up task…", "response_type": "ephemeral"})
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        text = command.get("text") or ""
        tid = parse_task_uuid(text)
        if tid is None:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Usage: `/status <task-id>` (UUID).",
            )
            return
        loop = asyncio.get_running_loop()
        try:
            row = await loop.run_in_executor(None, partial(get_task_status_sync, user_id, tid))
        except Exception as exc:  # noqa: BLE001
            log.exception("slack_status_failed", error=str(exc))
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Could not load task: {exc}",
            )
            return
        if row is None:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Task not found or access denied.",
            )
            return
        lines = [f"*{k}*: `{v}`" for k, v in row.items()]
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="Task status:\n" + "\n".join(lines),
        )

    @slack_app.command("/cancel")
    async def _cancel(ack, command, client):  # type: ignore[no-untyped-def]
        await ack({"text": "Requesting cancel…", "response_type": "ephemeral"})
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        text = command.get("text") or ""
        tid = parse_task_uuid(text)
        if tid is None:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Usage: `/cancel <task-id>` (UUID).",
            )
            return
        loop = asyncio.get_running_loop()
        try:
            ok, code = await loop.run_in_executor(None, partial(cancel_task_sync, user_id, tid))
        except Exception as exc:  # noqa: BLE001
            log.exception("slack_cancel_failed", error=str(exc))
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Could not cancel: {exc}",
            )
            return
        if not ok:
            if code == "not_found":
                msg = "Task not found or access denied."
            else:
                msg = f"Cancel failed ({code})."
            await client.chat_postEphemeral(channel=channel_id, user=user_id, text=msg)
            return
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"Cancel requested for `{tid}`.",
        )

    @slack_app.command("/history")
    async def _history(ack, command, client):  # type: ignore[no-untyped-def]
        await ack({"text": "Loading history…", "response_type": "ephemeral"})
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        loop = asyncio.get_running_loop()
        try:
            rows = await loop.run_in_executor(None, partial(list_task_history_sync, user_id))
        except Exception as exc:  # noqa: BLE001
            log.exception("slack_history_failed", error=str(exc))
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Could not load history: {exc}",
            )
            return
        if not rows:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="No tasks yet.",
            )
            return
        lines = [f"• `{r['id']}` — {r['status']} ({r['type']}) — {r['created_at']}" for r in rows]
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="Recent tasks:\n" + "\n".join(lines),
        )
