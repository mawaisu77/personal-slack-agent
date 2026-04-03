"""Post-navigation checks (T-022)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NavigationExpectation:
    """Optional checks after ``goto`` / client-side nav."""

    url_regex: str | None = None
    path_contains: str | None = None
    title_contains: str | None = None


def validate_navigation(page: Any, expectation: NavigationExpectation | None) -> tuple[bool, str]:
    """
    Verify URL (and optionally title) after navigation.

    SPA limitation: same URL may change content without failing ``path_contains``;
    combine with DOM capture in the agent loop when needed.
    """
    if expectation is None:
        return True, "skipped"

    url = getattr(page, "url", "") or ""
    if expectation.path_contains and expectation.path_contains not in url:
        return False, f"path_missing:{expectation.path_contains!r}"

    if expectation.url_regex:
        if not re.search(expectation.url_regex, url):
            return False, f"url_regex_mismatch:{url!r}"

    if expectation.title_contains:
        title = ""
        try:
            title = page.title()  # type: ignore[union-attr]
        except Exception:
            title = ""
        if expectation.title_contains not in title:
            return False, f"title_missing:{expectation.title_contains!r}"

    return True, "ok"
