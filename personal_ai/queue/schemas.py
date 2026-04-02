from __future__ import annotations

import json
import uuid
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from personal_ai.queue.errors import PayloadTooLargeError


class JobPayload(BaseModel):
    """Queue message body matching PRD §4 (T-003)."""

    model_config = ConfigDict(extra="forbid")

    MAX_BYTES: ClassVar[int] = 256 * 1024

    task_id: uuid.UUID
    user_id: str = Field(..., min_length=1, max_length=128)
    type: Literal["web", "call"]
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    retries: int = Field(default=0, ge=0)

    def to_redis_body(self) -> bytes:
        """Serialize for Redis; enforces max size."""
        raw = self.model_dump_json().encode("utf-8")
        if len(raw) > self.MAX_BYTES:
            raise PayloadTooLargeError(self.MAX_BYTES, len(raw))
        return raw

    @classmethod
    def from_redis_body(cls, body: bytes) -> JobPayload:
        if len(body) > cls.MAX_BYTES:
            raise PayloadTooLargeError(cls.MAX_BYTES, len(body))
        data = json.loads(body.decode("utf-8"))
        return cls.model_validate(data)
