"""Register the `/do` slash command (T-033)."""

from __future__ import annotations

import asyncio
from functools import partial

from slack_bolt.async_app import AsyncApp

from personal_ai.observability.logging import get_logger
from personal_ai.slack_interface.tasks import submit_web_task_sync

log = get_logger(__name__)


def register_do_command(slack_app: AsyncApp) -> None:
    @slack_app.command("/do")
    async def _handle_do(ack, command, client):  # type: ignore[no-untyped-def]
        await ack({"text": "Queuing your web task…", "response_type": "ephemeral"})
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        text = (command.get("text") or "").strip()
        loop = asyncio.get_running_loop()
        try:
            tid = await loop.run_in_executor(
                None,
                partial(submit_web_task_sync, user_id, text, slack_channel_id=channel_id),
            )
            msg = f"Queued task `{tid}`"
            if text:
                msg += f" — goal: {text[:500]}"
            await client.chat_postEphemeral(channel=channel_id, user=user_id, text=msg)
        except Exception as exc:  # noqa: BLE001
            log.exception("slack_do_failed", error=str(exc))
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Could not queue task: {exc}",
            )
