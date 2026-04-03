from __future__ import annotations

from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncApp

from personal_ai.config.secrets import get_secret
from personal_ai.observability.logging import get_logger
from personal_ai.slack_interface.approval_interactive import register_approval_handlers
from personal_ai.slack_interface.call_command import register_call_command
from personal_ai.slack_interface.do_command import register_do_command
from personal_ai.slack_interface.query_commands import register_query_commands

log = get_logger(__name__)


def create_app() -> FastAPI:
    """
    HTTP app: health + Slack Events API (T-016).

    Uses get_secret for SLACK_SIGNING_SECRET and SLACK_BOT_TOKEN (env or AWS bundle).
    """
    signing_secret = get_secret("SLACK_SIGNING_SECRET")
    bot_token = get_secret("SLACK_BOT_TOKEN")
    slack_app = AsyncApp(
        signing_secret=signing_secret,
        token=bot_token,
        process_before_response=True,
    )

    @slack_app.event("message")
    async def _on_message(_, ack) -> None:
        await ack()

    register_do_command(slack_app)
    register_call_command(slack_app)
    register_query_commands(slack_app)
    register_approval_handlers(slack_app)

    handler = AsyncSlackRequestHandler(slack_app)
    api = FastAPI(title="Personal AI Assistant — Slack gateway")

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/slack/events")
    async def slack_events(req: Request):
        return await handler.handle(req)

    log.info("slack_app_ready", routes=["/health", "/slack/events"])
    return api
