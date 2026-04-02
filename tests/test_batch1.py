from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from personal_ai.config.secrets import MissingSecretError, clear_secret_cache, get_secret
from personal_ai.config.settings import get_settings, reset_settings_cache
from personal_ai.observability.context import clear_context, get_task_id, get_user_id, task_context
from personal_ai.observability.logging import configure_logging, get_logger
from personal_ai.state.models import TaskStatus, TaskType


def test_task_enums_match_prd() -> None:
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.WAITING_FOR_APPROVAL.value == "waiting_for_approval"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.CANCELLED.value == "cancelled"
    assert {t.value for t in TaskType} == {"web", "call"}


def test_get_secret_env_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_settings_cache()
    clear_secret_cache()
    monkeypatch.setenv("SECRETS_MODE", "env")
    monkeypatch.setenv("TEST_SECRET", "hello")
    get_settings.cache_clear()
    assert get_secret("TEST_SECRET") == "hello"


def test_get_secret_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_settings_cache()
    clear_secret_cache()
    monkeypatch.setenv("SECRETS_MODE", "env")
    monkeypatch.delenv("MISSING_XYZ", raising=False)
    get_settings.cache_clear()
    with pytest.raises(MissingSecretError):
        get_secret("MISSING_XYZ")


def test_get_secret_aws_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_settings_cache()
    clear_secret_cache()
    monkeypatch.setenv("SECRETS_MODE", "aws")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_APP_SECRET_ID", "test/secret")
    get_settings.cache_clear()

    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {
        "SecretString": json.dumps({"MY_KEY": "from-aws"}),
    }
    with patch("boto3.client", return_value=mock_client):
        assert get_secret("MY_KEY") == "from-aws"


def test_structlog_includes_task_and_user_ids(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    configure_logging(json_logs=True)
    clear_context()
    log = get_logger("test")
    with task_context("task-123", "U456"):
        log.info("hello_event", extra_field=1)
    out = capsys.readouterr().out
    line = json.loads(out.strip().splitlines()[-1])
    assert line.get("task_id") == "task-123"
    assert line.get("user_id") == "U456"
    assert line.get("event") == "hello_event"


def test_context_cleared_outside_block() -> None:
    configure_logging(json_logs=False)
    clear_context()
    with task_context("t1", "u1"):
        assert get_task_id() == "t1"
        assert get_user_id() == "u1"
    assert get_task_id() is None
    assert get_user_id() is None
