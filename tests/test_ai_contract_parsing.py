"""T-048: AI response schema validation and action shape coverage."""

from __future__ import annotations

import json

import pytest

from personal_ai.run.ai_contract import ValidationFailedError, parse_ai_response


def _valid_action(**kwargs: object) -> dict:
    base = {
        "action": "wait",
        "target": "",
        "value": "0.1",
        "confidence": 1.0,
        "reason": "test",
    }
    base.update(kwargs)
    return {
        "reasoning": "because",
        "action": base,
    }


def test_parse_minimal_valid_response() -> None:
    raw = json.dumps(_valid_action())
    out = parse_ai_response(raw)
    assert out["reasoning"] == "because"
    assert out["action"]["action"] == "wait"


def test_parse_goal_reached_optional() -> None:
    d = _valid_action()
    body = {"reasoning": "r", "action": d["action"], "goal_reached": True}
    out = parse_ai_response(json.dumps(body))
    assert out.get("goal_reached") is True


def test_parse_requires_approval_on_action() -> None:
    a = _valid_action()["action"]
    a["requires_approval"] = True
    out = parse_ai_response(json.dumps({"reasoning": "r", "action": a}))
    assert out["action"]["requires_approval"] is True


def test_reject_invalid_action_enum() -> None:
    a = _valid_action()["action"]
    a["action"] = "invalid"
    with pytest.raises(ValidationFailedError):
        parse_ai_response(json.dumps({"reasoning": "r", "action": a}))


def test_reject_missing_reasoning() -> None:
    with pytest.raises(ValidationFailedError):
        parse_ai_response(json.dumps({"action": _valid_action()["action"]}))


def test_reject_additional_top_level_property() -> None:
    body = _valid_action()
    body["extra"] = "nope"
    with pytest.raises(ValidationFailedError):
        parse_ai_response(json.dumps(body))


def test_reject_non_object() -> None:
    with pytest.raises(ValidationFailedError):
        parse_ai_response("[1,2,3]")
