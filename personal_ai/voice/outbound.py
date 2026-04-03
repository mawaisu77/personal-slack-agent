from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from personal_ai.voice.provider import VoiceProvider


@dataclass(frozen=True)
class OutboundCallResult:
    success: bool
    call_id: str | None
    reason: str | None = None


class OutboundCallService:
    """Outbound call execution wrapper (T-029)."""

    def __init__(self, provider: VoiceProvider) -> None:
        self._provider = provider

    def place_call(
        self,
        to_number: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> OutboundCallResult:
        try:
            call_id = self._provider.start_call(to_number, metadata=metadata)
            return OutboundCallResult(success=True, call_id=call_id)
        except Exception as exc:  # noqa: BLE001
            return OutboundCallResult(success=False, call_id=None, reason=str(exc))
