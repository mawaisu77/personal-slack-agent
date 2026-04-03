from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from personal_ai.approvals.expiry import expire_overdue_approvals
from personal_ai.approvals.policy import (
    ApprovalPolicy,
    apply_policy_to_action,
    load_policy_from_path,
)
from personal_ai.config.settings import reset_settings_cache
from personal_ai.orchestrator.budget import BudgetExceededError, BudgetService


def test_approval_policy_regex_matches_target() -> None:
    p = ApprovalPolicy(
        target_regex=[re.compile("dangerous", re.I)],
        action_types=frozenset({"click"}),
    )
    action = {"action": "click", "target": "#dangerous-btn", "confidence": 1, "reason": "x"}
    assert p.requires(action) is True


def test_apply_policy_sets_requires_approval() -> None:
    p = ApprovalPolicy(
        target_regex=[re.compile("pay", re.I)],
        action_types=frozenset(),
    )
    action = {"action": "click", "target": "pay-now", "confidence": 1, "reason": "x"}
    apply_policy_to_action(action, p)
    assert action.get("requires_approval") is True


def test_load_policy_from_file(tmp_path: Path) -> None:
    path = tmp_path / "p.json"
    path.write_text(
        json.dumps(
            {
                "target_regex": ["submit"],
                "reason_regex": [],
                "action_types": ["click"],
            },
        ),
        encoding="utf-8",
    )
    p = load_policy_from_path(path)
    assert "submit" in [x.pattern for x in p.target_regex]


def test_expire_overdue_no_pending_rows() -> None:
    session = MagicMock()
    session.scalars.return_value.all.return_value = []
    assert expire_overdue_approvals(session) == 0


def test_budget_exceeds_concurrent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_CONCURRENT_TASKS_PER_USER", "2")
    reset_settings_cache()
    session = MagicMock()
    session.scalar.return_value = 2
    bs = BudgetService(session)
    with pytest.raises(BudgetExceededError) as exc:
        bs.enforce_user_limits("U1")
    assert exc.value.code == "CONCURRENT_CAP"
    reset_settings_cache()


def test_budget_exceeds_daily(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_DAILY_TASKS_PER_USER", "5")
    monkeypatch.setenv("MAX_CONCURRENT_TASKS_PER_USER", "0")
    reset_settings_cache()
    session = MagicMock()
    session.scalar.return_value = 5
    bs = BudgetService(session)
    with pytest.raises(BudgetExceededError) as exc:
        bs.enforce_user_limits("U1")
    assert exc.value.code == "DAILY_CAP"
    reset_settings_cache()
