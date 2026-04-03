from __future__ import annotations

from typing import Any

from personal_ai.observability.logging import get_logger

log = get_logger(__name__)


def capture_page_state(page: Any, *, max_dom_chars: int = 50000) -> dict[str, Any]:
    """
    Capture DOM + screenshot bytes for the agent loop (T-018).
    page must expose `.content()` and `.screenshot()`.
    """
    dom = page.content()
    truncated = False
    if len(dom) > max_dom_chars:
        dom = dom[:max_dom_chars]
        truncated = True
        log.warning("dom_truncated", max_dom_chars=max_dom_chars)
    screenshot = page.screenshot(type="png", full_page=True)
    return {"dom": dom, "screenshot_png": screenshot, "truncated": truncated}
