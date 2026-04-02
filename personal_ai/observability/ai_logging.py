"""
AI prompt/completion logging with redaction (T-044).

Masks common secret patterns and truncates large blobs before emit.
"""

from __future__ import annotations

import re
from typing import Any

from personal_ai.observability.context import get_task_id, get_user_id
from personal_ai.observability.logging import get_logger

log = get_logger(__name__)

_DEFAULT_MAX = 4096
_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._-]{10,}", re.I),
)


def redact_text(text: str, *, max_chars: int = _DEFAULT_MAX) -> str:
    """Redact sensitive substrings and truncate."""
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    if len(out) > max_chars:
        return out[:max_chars] + f"... [truncated {len(out) - max_chars} chars]"
    return out


def redact_value(value: Any, *, max_chars: int = _DEFAULT_MAX) -> Any:
    """Recursively redact dict/list/str leaves."""
    if isinstance(value, str):
        return redact_text(value, max_chars=max_chars)
    if isinstance(value, dict):
        return {k: redact_value(v, max_chars=max_chars) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(v, max_chars=max_chars) for v in value]
    return value


def log_ai_io(
    *,
    model: str | None,
    prompt: Any,
    completion: Any,
    extra: dict[str, Any] | None = None,
) -> None:
    """Structured log line for one model turn (sanitized)."""
    tid = get_task_id()
    uid = get_user_id()
    fields: dict[str, Any] = {
        "model": model,
        "prompt": redact_value(prompt),
        "completion": redact_value(completion),
    }
    if tid:
        fields["task_id"] = tid
    if uid:
        fields["user_id"] = uid
    if extra:
        fields["extra"] = redact_value(extra)
    log.info("ai_io", **fields)
