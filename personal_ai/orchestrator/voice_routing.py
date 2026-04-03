"""Call-type jobs use the voice pipeline (T-032)."""

from __future__ import annotations

from personal_ai.queue.schemas import JobPayload

VOICE_JOB_TYPE = "call"


def is_voice_job(job: JobPayload) -> bool:
    return job.type == VOICE_JOB_TYPE
