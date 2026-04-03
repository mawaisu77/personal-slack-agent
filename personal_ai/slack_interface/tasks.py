"""Slack-triggered task submission (sync; call via asyncio.to_thread from Bolt)."""

from __future__ import annotations

import uuid

from personal_ai.config.settings import get_settings
from personal_ai.db.session import session_scope
from personal_ai.orchestrator.dispatch import OrchestratorDispatchService
from personal_ai.queue.redis_queue import RedisJobQueue, get_redis_client
from personal_ai.state.models import TaskType


def submit_web_task_sync(
    user_id: str,
    goal: str,
    *,
    slack_channel_id: str | None = None,
) -> uuid.UUID:
    """Enqueue a web automation task (T-033). Optional Slack channel for T-036 progress."""
    settings = get_settings()
    r = get_redis_client(settings.redis_url)
    q = RedisJobQueue(r)
    payload: dict[str, str] = {"goal": goal}
    if slack_channel_id:
        payload["slack_channel_id"] = slack_channel_id
    with session_scope() as session:
        orch = OrchestratorDispatchService(session, q)
        task = orch.submit_task(
            user_id=user_id,
            task_type=TaskType.WEB,
            payload=payload,
        )
        return task.id


def submit_call_task_sync(
    user_id: str,
    phone: str,
    *,
    slack_channel_id: str | None = None,
) -> uuid.UUID:
    """Enqueue a voice call task; worker routes via voice pipeline (T-032, T-034)."""
    settings = get_settings()
    r = get_redis_client(settings.redis_url)
    q = RedisJobQueue(r)
    payload: dict[str, str] = {"phone": phone.strip()}
    if slack_channel_id:
        payload["slack_channel_id"] = slack_channel_id
    with session_scope() as session:
        orch = OrchestratorDispatchService(session, q)
        task = orch.submit_task(
            user_id=user_id,
            task_type=TaskType.CALL,
            payload=payload,
        )
        return task.id
