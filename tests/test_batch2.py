from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from personal_ai.config.settings import reset_settings_cache
from personal_ai.orchestrator.lifecycle import ALLOWED_TRANSITIONS, transition_allowed
from personal_ai.queue.errors import PayloadTooLargeError
from personal_ai.queue.schemas import JobPayload
from personal_ai.run.ai_contract import (
    ValidationFailedError,
    parse_ai_response,
    with_validation_retries,
)
from personal_ai.slack_interface import create_app
from personal_ai.state.models import TaskStatus


def _slack_sig(secret: str, timestamp: str, body: str) -> str:
    basestring = f"v0:{timestamp}:{body}"
    digest = hmac.new(secret.encode(), basestring.encode(), hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_transition_matrix_covers_prd_states() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(TaskStatus)


def test_terminal_states_immutable() -> None:
    for s in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        assert ALLOWED_TRANSITIONS[s] == frozenset()


def test_pending_to_running_allowed() -> None:
    assert transition_allowed(TaskStatus.PENDING, TaskStatus.RUNNING) is True


def test_completed_to_running_rejected() -> None:
    assert transition_allowed(TaskStatus.COMPLETED, TaskStatus.RUNNING) is False


def test_job_payload_roundtrip() -> None:
    tid = uuid.uuid4()
    p = JobPayload(
        task_id=tid,
        user_id="U123",
        type="web",
        payload={"goal": "open example.com"},
        priority=2,
        retries=1,
    )
    body = p.to_redis_body()
    q = JobPayload.from_redis_body(body)
    assert q.task_id == tid
    assert q.type == "web"
    assert q.priority == 2


def test_job_payload_too_large() -> None:
    huge = "x" * (JobPayload.MAX_BYTES + 10)
    p = JobPayload(
        task_id=uuid.uuid4(),
        user_id="U1",
        type="call",
        payload={"blob": huge},
    )
    with pytest.raises(PayloadTooLargeError):
        p.to_redis_body()


def test_ai_response_valid() -> None:
    raw = {
        "reasoning": "Button is visible",
        "action": {
            "action": "click",
            "target": "button.submit",
            "confidence": 0.9,
            "reason": "Matches goal",
        },
    }
    out = parse_ai_response(raw)
    assert out["reasoning"] == "Button is visible"


def test_ai_response_missing_reasoning() -> None:
    bad = {"action": {"action": "wait", "target": "x", "confidence": 1, "reason": "r"}}
    with pytest.raises(ValidationFailedError):
        parse_ai_response(bad)


def test_with_validation_retries_succeeds_second_attempt() -> None:
    attempts: list[int] = []

    def fetch() -> str:
        attempts.append(1)
        if len(attempts) < 2:
            return '{"not":"valid"}'
        return json.dumps(
            {
                "reasoning": "ok",
                "action": {
                    "action": "wait",
                    "target": "body",
                    "confidence": 0.5,
                    "reason": "pause",
                },
            }
        )

    out = with_validation_retries(fetch, max_attempts=3)
    assert out["reasoning"] == "ok"
    assert len(attempts) == 2


def test_with_validation_retries_exhausted() -> None:
    def fetch() -> str:
        return "{}"

    with pytest.raises(ValidationFailedError):
        with_validation_retries(fetch, max_attempts=2)


def test_slack_health(slack_app_env: None) -> None:
    reset_settings_cache()
    app = create_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_slack_url_verification(slack_app_env: None) -> None:
    reset_settings_cache()
    app = create_app()
    client = TestClient(app)
    body_dict = {"type": "url_verification", "challenge": "challenge-token-xyz"}
    body = json.dumps(body_dict)
    ts = str(int(time.time()))
    headers = {
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": _slack_sig("test-slack-signing-secret", ts, body),
    }
    r = client.post("/slack/events", content=body.encode("utf-8"), headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("challenge") == "challenge-token-xyz"


def test_slack_bad_signature_rejected(slack_app_env: None) -> None:
    reset_settings_cache()
    app = create_app()
    client = TestClient(app)
    body = '{"type":"url_verification","challenge":"x"}'
    headers = {
        "X-Slack-Request-Timestamp": str(int(time.time())),
        "X-Slack-Signature": "v0=deadbeef",
    }
    r = client.post("/slack/events", content=body.encode("utf-8"), headers=headers)
    assert r.status_code in (401, 403)
