from __future__ import annotations

from personal_ai.config.settings import Settings, get_settings
from personal_ai.voice.provider import NoopVoiceProvider, VoiceProvider


def get_voice_provider(settings: Settings | None = None) -> VoiceProvider:
    """Config-driven provider selection (extend with Vapi/Bland/Retell clients)."""
    s = settings or get_settings()
    if s.voice_provider == "noop":
        return NoopVoiceProvider()
    msg = f"Voice provider not implemented: {s.voice_provider}"
    raise NotImplementedError(msg)
