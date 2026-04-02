from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class VoiceProvider(ABC):
    """Outbound voice abstraction (Vapi / Bland / Retell) — T-028."""

    @abstractmethod
    def start_call(self, to_number: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Begin outbound call; returns provider call id."""

    @abstractmethod
    def end_call(self, call_id: str) -> None:
        """Tear down an active call."""

    def on_event(self, _handler: Callable[[dict[str, Any]], None]) -> None:
        """Register for provider events (stub until realtime wiring)."""


class NoopVoiceProvider(VoiceProvider):
    """Default provider: no telephony; for local/dev."""

    def start_call(self, to_number: str, *, metadata: dict[str, Any] | None = None) -> str:
        _ = (to_number, metadata)
        return f"noop-{uuid.uuid4()}"

    def end_call(self, call_id: str) -> None:
        _ = call_id
