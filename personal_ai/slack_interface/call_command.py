"""Register the `/call` slash command (T-034)."""

from __future__ import annotations

import asyncio
from functools import partial

from slack_bolt.async_app import AsyncApp

from personal_ai.observability.logging import get_logger
from personal_ai.slack_interface.tasks import submit_call_task_sync
from personal_ai.voice.phone import resolve_phone_e164

log = get_logger(__name__)


def register_call_command(slack_app: AsyncApp) -> None:
    @slack_app.command("/call")
    async def _handle_call(ack, command, client):  # type: ignore[no-untyped-def]
        await ack({"text": "Queuing your call…", "response_type": "ephemeral"})
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        text = (command.get("text") or "").strip()
        if not text:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Usage: `/call +1 555 555 0199` (E.164 or US digits).",
            )
            return
        try:
            resolve_phone_e164({"phone": text})
        except ValueError as exc:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Invalid phone number: {exc}",
            )
            return
        loop = asyncio.get_running_loop()
        try:
            tid = await loop.run_in_executor(
                None,
                partial(submit_call_task_sync, user_id, text, slack_channel_id=channel_id),
            )
            msg = f"Queued call task `{tid}` — {text[:200]}"
            await client.chat_postEphemeral(channel=channel_id, user=user_id, text=msg)
        except Exception as exc:  # noqa: BLE001
            log.exception("slack_call_failed", error=str(exc))
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Could not queue call: {exc}",
            )
