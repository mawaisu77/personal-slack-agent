"""Redacted context views for agent prompts (T-043)."""

from __future__ import annotations

import copy
import re
from typing import TYPE_CHECKING, Any

_SENSITIVE_KEY = re.compile(
    r"(password|secret|token|api[_-]?key|authorization|auth|credential|ssn|credit)",
    re.IGNORECASE,
)


def _redact_value(v: Any) -> Any:
    if isinstance(v, str) and v:
        return "***"
    if isinstance(v, dict):
        return redact_json(v)
    if isinstance(v, list):
        return [redact_json(x) if isinstance(x, dict) else _redact_value(x) for x in v]
    return v


def redact_json(obj: dict[str, Any]) -> dict[str, Any]:
    """Deep copy with sensitive keys masked."""
    out: dict[str, Any] = copy.deepcopy(obj)
    stack: list[dict[str, Any]] = [out]
    while stack:
        cur = stack.pop()
        for k in list(cur.keys()):
            if _SENSITIVE_KEY.search(k):
                cur[k] = "***"
            elif isinstance(cur[k], dict):
                stack.append(cur[k])
            elif isinstance(cur[k], list):
                cur[k] = [
                    redact_json(x) if isinstance(x, dict) else _redact_value(x) for x in cur[k]
                ]
    return out


if TYPE_CHECKING:
    from personal_ai.context_store.store import ContextStore


class MaskedContextStore:
    """Wraps ``ContextStore``; ``get`` returns rows with redacted ``value_json``."""

    def __init__(self, inner: ContextStore) -> None:
        self._inner = inner

    def get(self, *, user_id: str, context_key: str) -> Any | None:
        row = self._inner.get(user_id=user_id, context_key=context_key)
        if row is None:
            return None
        clone = copy.copy(row)
        clone.value_json = redact_json(dict(row.value_json))
        return clone

    def upsert(self, *args: Any, **kwargs: Any) -> Any:
        return self._inner.upsert(*args, **kwargs)
