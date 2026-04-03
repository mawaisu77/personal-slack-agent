from __future__ import annotations

import os

import pytest

from personal_ai.run.progress_signals import state_fingerprint


def test_state_fingerprint_dom_and_png() -> None:
    a = state_fingerprint({"dom": "<html>a</html>", "screenshot_png": b"x"})
    b = state_fingerprint({"dom": "<html>b</html>", "screenshot_png": b"x"})
    assert a != b


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("RUN_BROWSER_INTEGRATION", "").lower() not in ("1", "true", "yes"),
    reason="Set RUN_BROWSER_INTEGRATION=1 and run `playwright install` to enable.",
)
def test_playwright_stub_ai_loop_completes() -> None:
    """T-049: real browser + deterministic JSON AI."""
    from playwright.sync_api import sync_playwright

    from personal_ai.run.agent_loop import default_stub_ai_fn, run_web_agent_loop

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(
                "data:text/html,<html><body><p>fixture</p></body></html>",
                wait_until="domcontentloaded",
            )
            r = run_web_agent_loop(
                page,
                goal="read page",
                ai_fn=default_stub_ai_fn("read page"),
                max_steps=5,
            )
            assert r.status == "completed"
        finally:
            browser.close()
