from __future__ import annotations

import contextvars
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

_task_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("task_id", default=None)
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)


def get_task_id() -> str | None:
    return _task_id.get()


def get_user_id() -> str | None:
    return _user_id.get()


def bind_context(*, task_id: str | None = None, user_id: str | None = None) -> None:
    if task_id is not None:
        _task_id.set(task_id)
    if user_id is not None:
        _user_id.set(user_id)


def clear_context() -> None:
    _task_id.set(None)
    _user_id.set(None)


@contextmanager
def task_context(task_id: str | None, user_id: str | None) -> Generator[None, None, None]:
    """Set task_id / user_id for the duration of a block (e.g. request or job handler)."""
    t_token = _task_id.set(task_id)
    u_token = _user_id.set(user_id)
    try:
        yield
    finally:
        _task_id.reset(t_token)
        _user_id.reset(u_token)


def context_dict() -> dict[str, Any]:
    """Key-value pairs merged into every log event."""
    out: dict[str, Any] = {}
    tid = get_task_id()
    uid = get_user_id()
    if tid is not None:
        out["task_id"] = tid
    if uid is not None:
        out["user_id"] = uid
    return out
