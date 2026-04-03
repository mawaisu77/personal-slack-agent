"""Configurable rules for when an action must go through human approval (T-040)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from personal_ai.config.settings import get_settings
from personal_ai.observability.logging import get_logger

log = get_logger(__name__)


@dataclass
class ApprovalPolicy:
    """
    Policy is merged with model output: if any rule matches, ``requires_approval`` is set True.

    Default: no automatic flags (model / explicit JSON still controls gating).
    """

    target_regex: list[re.Pattern[str]] = field(default_factory=list)
    reason_regex: list[re.Pattern[str]] = field(default_factory=list)
    action_types: frozenset[str] = field(default_factory=frozenset)

    def requires(self, action: dict[str, Any]) -> bool:
        kind = str(action.get("action", ""))
        if self.action_types and kind not in self.action_types:
            return False
        target = str(action.get("target", ""))
        reason = str(action.get("reason", ""))
        for rx in self.target_regex:
            if rx.search(target):
                return True
        for rx in self.reason_regex:
            if rx.search(reason):
                return True
        return False


def _compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    out: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            out.append(re.compile(p, re.IGNORECASE))
        except re.error as exc:
            log.warning("approval_policy_bad_regex", pattern=p, error=str(exc))
    return out


def load_policy_from_path(path: Path) -> ApprovalPolicy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ApprovalPolicy(
        target_regex=_compile_patterns(list(raw.get("target_regex", []))),
        reason_regex=_compile_patterns(list(raw.get("reason_regex", []))),
        action_types=frozenset(raw.get("action_types", []) or []),
    )


def get_default_approval_policy() -> ApprovalPolicy:
    """Load from ``APPROVAL_POLICY_PATH`` when set; otherwise empty policy."""
    settings = get_settings()
    p = settings.approval_policy_path
    if not p:
        return ApprovalPolicy()
    path = Path(p)
    if not path.is_file():
        log.warning("approval_policy_missing_file", path=str(path))
        return ApprovalPolicy()
    try:
        return load_policy_from_path(path)
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("approval_policy_load_failed", path=str(path), error=str(exc))
        return ApprovalPolicy()


def apply_policy_to_action(action: dict[str, Any], policy: ApprovalPolicy | None) -> dict[str, Any]:
    """Mutates and returns ``action`` when policy demands approval (T-040)."""
    if policy is None:
        return action
    if policy.requires(action):
        action["requires_approval"] = True
    return action
