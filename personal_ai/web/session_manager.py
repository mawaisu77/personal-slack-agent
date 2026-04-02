"""
Playwright: one browser per process, isolated ``BrowserContext`` per ``task_id`` (T-017).

``user_data_dir`` is reserved for future ``storage_state`` load/save; contexts are isolated
so cookies from one task do not leak to another.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from personal_ai.config.settings import get_settings

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Playwright


class PlaywrightSessionManager:
    def __init__(self, user_data_dir: Path | str | None = None) -> None:
        settings = get_settings()
        self._user_data_dir = Path(user_data_dir or settings.playwright_user_data_dir)
        self._user_data_dir.mkdir(parents=True, exist_ok=True)
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._contexts: dict[str, BrowserContext] = {}

    def start(self) -> None:
        from playwright.sync_api import sync_playwright

        if self._browser is not None:
            return
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)

    def new_context_for_task(self, task_id: str):
        """New browser context for this task (no shared cookies/storage with other tasks)."""
        if self._browser is None:
            self.start()
        assert self._browser is not None
        ctx = self._browser.new_context()
        self._contexts[task_id] = ctx
        return ctx

    def close_context_for_task(self, task_id: str) -> None:
        ctx = self._contexts.pop(task_id, None)
        if ctx is not None:
            ctx.close()

    def shutdown(self) -> None:
        for tid in list(self._contexts):
            self.close_context_for_task(tid)
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._pw is not None:
            self._pw.stop()
            self._pw = None
