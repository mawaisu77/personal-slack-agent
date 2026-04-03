import pytest

from personal_ai.observability.logging import configure_logging


@pytest.fixture(autouse=True)
def reset_logging() -> None:
    """
    Keep structlog bound to a live stdout per test.
    Some tests switch JSON console mode, which otherwise leaks PrintLogger state.
    """
    configure_logging(json_logs=False)
    yield
    configure_logging(json_logs=False)


@pytest.fixture
def slack_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bolt requires signing secret + bot token for AsyncApp (T-016 tests)."""
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-slack-signing-secret")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-dummy-token")
