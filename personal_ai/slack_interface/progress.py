"""Throttled Slack progress for long-running tasks (T-036)."""

from __future__ import annotations

import time
import uuid

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from personal_ai.config.secrets import get_secret
from personal_ai.observability.logging import get_logger

log = get_logger(__name__)

# PRD §16: surface progress for work longer than ~30s without spamming the API.
_MIN_INTERVAL_SEC = 30.0


class SlackProgressNotifier:
    """Posts ephemeral updates; throttles to roughly once per ``_MIN_INTERVAL_SEC``."""

    def __init__(
        self,
        *,
        user_id: str,
        channel_id: str,
        task_id: uuid.UUID,
        min_interval_sec: float = _MIN_INTERVAL_SEC,
    ) -> None:
        self._user_id = user_id
        self._channel_id = channel_id
        self._task_id = task_id
        self._min_interval = min_interval_sec
        self._last_post = 0.0

    def maybe_post(self, step: int, message: str) -> None:
        now = time.monotonic()
        first = step <= 1
        if not first and (now - self._last_post) < self._min_interval:
            return
        self._last_post = now
        text = f"[task `{self._task_id}`] step {step}: {message[:800]}"
        try:
            token = get_secret("SLACK_BOT_TOKEN")
            client = WebClient(token=token)
            client.chat_postEphemeral(
                channel=self._channel_id,
                user=self._user_id,
                text=text,
            )
        except SlackApiError as exc:
            log.warning("slack_progress_post_failed", error=str(exc))
        except Exception as exc:  # noqa: BLE001
            log.warning("slack_progress_unexpected", error=str(exc))


def post_task_terminal_note(
    *,
    user_id: str,
    channel_id: str,
    task_id: uuid.UUID,
    summary: str,
) -> None:
    """Optional final ping (not throttled)."""
    text = f"[task `{task_id}`] finished: {summary[:1000]}"
    try:
        token = get_secret("SLACK_BOT_TOKEN")
        client = WebClient(token=token)
        client.chat_postEphemeral(channel=channel_id, user=user_id, text=text)
    except SlackApiError as exc:
        log.warning("slack_terminal_post_failed", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        log.warning("slack_terminal_unexpected", error=str(exc))
