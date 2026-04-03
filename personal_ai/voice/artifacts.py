"""Voice call artifacts merged into task payload (T-031)."""

from __future__ import annotations

from typing import Any


def merge_voice_artifacts(
    payload: dict[str, Any],
    *,
    transcript: str | None = None,
    summary: str | None = None,
    call_id: str | None = None,
) -> dict[str, Any]:
    """Return a shallow copy of ``payload`` with ``voice`` sub-document updated."""
    out = dict(payload)
    voice: dict[str, Any] = dict(out.get("voice") or {})
    if transcript is not None:
        voice["transcript"] = transcript
    if summary is not None:
        voice["summary"] = summary
    if call_id is not None:
        voice["call_id"] = call_id
    out["voice"] = voice
    return out
