import pytest


@pytest.fixture
def slack_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bolt requires signing secret + bot token for AsyncApp (T-016 tests)."""
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-slack-signing-secret")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-dummy-token")
