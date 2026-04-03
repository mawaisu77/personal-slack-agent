"""DOM + screenshot fingerprints for no-progress and no-op detection (T-024, T-026)."""

from __future__ import annotations

import hashlib
from typing import Any


def state_fingerprint(capture: dict[str, Any]) -> int:
    """
    Stable-ish fingerprint from captured page state.

    Mixes truncated DOM text and PNG bytes so static DOM + changed pixels still moves
    the fingerprint (T-024).
    """
    dom = str(capture.get("dom", ""))[:12_000]
    png = bytes(capture.get("screenshot_png") or b"")[:50_000]
    h = hashlib.sha256()
    h.update(dom.encode("utf-8", errors="replace"))
    h.update(png)
    return int.from_bytes(h.digest()[:8], "big")
