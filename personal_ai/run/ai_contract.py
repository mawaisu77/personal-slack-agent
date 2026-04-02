from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

from jsonschema import Draft202012Validator

from personal_ai.observability.logging import get_logger

log = get_logger(__name__)

# PRD §5.2 (action) + §6 (reasoning wrapper)
_ACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["action", "target", "confidence", "reason"],
    "properties": {
        "action": {
            "type": "string",
            "enum": ["click", "type", "scroll", "wait", "extract"],
        },
        "target": {"type": "string", "minLength": 1},
        "value": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

AI_RESPONSE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AIResponse",
    "type": "object",
    "required": ["reasoning", "action"],
    "properties": {
        "reasoning": {"type": "string", "minLength": 1},
        "action": _ACTION_SCHEMA,
    },
    "additionalProperties": False,
}

_validator = Draft202012Validator(AI_RESPONSE_SCHEMA)


class ValidationFailedError(ValueError):
    """AI output failed JSON schema validation (T-014)."""


def parse_ai_response(raw: str | bytes | dict[str, Any]) -> dict[str, Any]:
    """Validate model output; raises ValidationFailedError on bad shape."""
    if isinstance(raw, (str, bytes)):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValidationFailedError("invalid JSON") from e
    else:
        data = raw
    if not isinstance(data, dict):
        raise ValidationFailedError("AI response must be a JSON object")
    errors = sorted(_validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        msg = errors[0].message
        raise ValidationFailedError(msg)
    return data


T = TypeVar("T")


def with_validation_retries(
    fetch: Callable[[], T],
    *,
    parse: Callable[[T], dict[str, Any]] = parse_ai_response,
    max_attempts: int = 3,
) -> dict[str, Any]:
    """Re-invoke fetch until output validates or attempts exhausted (T-014)."""
    last: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            raw = fetch()
            return parse(raw)
        except ValidationFailedError as e:
            last = e
            log.warning(
                "ai_response_validation_retry",
                attempt=attempt,
                max_attempts=max_attempts,
                error=str(e),
            )
    assert last is not None
    raise last
