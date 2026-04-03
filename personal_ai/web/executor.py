"""Execute validated AI actions against a Playwright page (T-020, T-021)."""

from __future__ import annotations

from typing import Any, TypedDict

from personal_ai.observability.logging import get_logger

log = get_logger(__name__)

MIN_INTERACTION_ATTEMPTS = 3


class ActionResult(TypedDict):
    ok: bool
    action: str
    detail: str | None


def execute_action(page: Any, action: dict[str, Any]) -> ActionResult:
    """
    Run one action from the AI contract (``personal_ai.run.ai_contract``).
    ``target`` is a CSS selector unless ``action`` is ``wait`` (seconds in ``value``).
    """
    kind = action["action"]
    target = action.get("target", "")
    value = action.get("value", "")

    if kind == "click":
        page.locator(target).first.click(timeout=30_000)
        return {"ok": True, "action": kind, "detail": None}

    if kind == "type":
        page.locator(target).first.fill(str(value), timeout=30_000)
        return {"ok": True, "action": kind, "detail": None}

    if kind == "scroll":
        page.locator(target).first.scroll_into_view_if_needed(timeout=30_000)
        return {"ok": True, "action": kind, "detail": None}

    if kind == "wait":
        ms = int(float(str(value).strip() or "1") * 1000)
        page.wait_for_timeout(ms)
        return {"ok": True, "action": kind, "detail": f"waited_ms={ms}"}

    if kind == "extract":
        text = page.locator(target).first.inner_text(timeout=30_000)
        return {"ok": True, "action": kind, "detail": text}

    return {"ok": False, "action": str(kind), "detail": "unknown_action"}


def execute_action_with_retry(
    page: Any,
    action: dict[str, Any],
    *,
    min_attempts: int = MIN_INTERACTION_ATTEMPTS,
) -> ActionResult:
    """
    Retry failed interactions at least ``min_attempts`` times (T-021).

    Retries on exceptions and on ``ok: False`` results from :func:`execute_action`.
    """
    if min_attempts < 1:
        raise ValueError("min_attempts must be >= 1")

    last: ActionResult | None = None
    for attempt in range(1, min_attempts + 1):
        try:
            last = execute_action(page, action)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "interaction_attempt_exception",
                attempt=attempt,
                max_attempts=min_attempts,
                action=action.get("action"),
                error=str(exc),
            )
            if attempt >= min_attempts:
                raise
            continue

        if last["ok"]:
            return last

        log.warning(
            "interaction_attempt_not_ok",
            attempt=attempt,
            max_attempts=min_attempts,
            action=last["action"],
            detail=last.get("detail"),
        )

    assert last is not None
    return last
