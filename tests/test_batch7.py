from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from personal_ai.run.agent_loop import default_stub_ai_fn, run_web_agent_loop
from personal_ai.run.ai_contract import parse_ai_response
from personal_ai.slack_interface.progress import SlackProgressNotifier
from personal_ai.slack_interface.tasks import submit_call_task_sync


def _mock_page_for_loop() -> MagicMock:
    page = MagicMock()
    page.url = "https://example.test/"
    page.content.return_value = "<html><body>hi</body></html>"
    page.screenshot.return_value = b"\x89PNG\x0d\x0a\x1a\x0a"
    loc = MagicMock()
    page.locator.return_value = loc
    loc.first.click.return_value = None
    loc.first.fill.return_value = None
    loc.first.scroll_into_view_if_needed.return_value = None
    loc.first.inner_text.return_value = "ok"
    return page


def test_run_web_agent_loop_stub_completes() -> None:
    page = _mock_page_for_loop()
    r = run_web_agent_loop(page, goal="open site", ai_fn=default_stub_ai_fn("open site"))
    assert r.status == "completed"
    assert r.steps >= 1


def test_run_web_agent_loop_no_progress() -> None:
    page = _mock_page_for_loop()

    def never_done(_ctx: dict) -> str:
        return json.dumps(
            {
                "reasoning": "keep waiting",
                "action": {
                    "action": "wait",
                    "target": "",
                    "value": "0.01",
                    "confidence": 1,
                    "reason": "hold",
                },
                "goal_reached": False,
            },
        )

    r = run_web_agent_loop(
        page,
        goal="x",
        ai_fn=never_done,
        no_progress_streak=3,
        max_steps=50,
    )
    assert r.status == "no_progress"


def test_parse_ai_response_goal_reached_optional() -> None:
    raw = json.dumps(
        {
            "reasoning": "r",
            "action": {
                "action": "wait",
                "target": "",
                "value": "1",
                "confidence": 1,
                "reason": "x",
            },
            "goal_reached": True,
        },
    )
    p = parse_ai_response(raw)
    assert p["goal_reached"] is True


def test_slack_progress_notifier_throttles() -> None:
    calls: list[str] = []

    def fake_post(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs.get("text", ""))
        return MagicMock()

    n = SlackProgressNotifier(
        user_id="U1",
        channel_id="C1",
        task_id=uuid.uuid4(),
        min_interval_sec=10_000.0,
    )
    with patch("personal_ai.slack_interface.progress.get_secret", return_value="x"):
        with patch("personal_ai.slack_interface.progress.WebClient") as WC:
            WC.return_value.chat_postEphemeral.side_effect = fake_post
            n.maybe_post(1, "a")
            n.maybe_post(2, "b")
            n.maybe_post(3, "c")
    assert len(calls) == 1


def test_submit_call_task_sync_includes_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    tid = uuid.uuid4()

    def fake_submit(self, **kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        t = MagicMock()
        t.id = tid
        return t

    monkeypatch.setattr(
        "personal_ai.slack_interface.tasks.OrchestratorDispatchService.submit_task",
        fake_submit,
    )

    @contextmanager
    def noop_scope():  # type: ignore[no-untyped-def]
        yield MagicMock()

    monkeypatch.setattr("personal_ai.slack_interface.tasks.session_scope", noop_scope)
    monkeypatch.setattr(
        "personal_ai.slack_interface.tasks.get_redis_client",
        lambda _url: fakeredis.FakeRedis(decode_responses=True),
    )

    out = submit_call_task_sync("U1", "+15555550123", slack_channel_id="C99")
    assert out == tid
    assert captured["payload"]["slack_channel_id"] == "C99"
