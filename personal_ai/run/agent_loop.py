"""Capture → AI → execute loop for web tasks (T-023, Batch 8 safety)."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from personal_ai.approvals.policy import (
    ApprovalPolicy,
    apply_policy_to_action,
    get_default_approval_policy,
)
from personal_ai.observability.logging import get_logger
from personal_ai.run.ai_contract import ValidationFailedError, with_validation_retries
from personal_ai.run.progress_signals import state_fingerprint
from personal_ai.web.capture import capture_page_state
from personal_ai.web.executor import execute_action_with_retry

if TYPE_CHECKING:
    from personal_ai.run.approval_workflow import ApprovalWorkflow

log = get_logger(__name__)

WebLoopStatus = Literal[
    "completed",
    "failed",
    "max_steps",
    "no_progress",
    "no_op",
    "timeout",
    "max_ai_calls",
    "invalid_ai_response",
    "approval_required_missing_channel",
]


@dataclass
class WebAgentLoopResult:
    status: WebLoopStatus
    steps: int
    ai_calls: int
    detail: str | None = None


def default_stub_ai_fn(_goal: str) -> Callable[[dict[str, Any]], str]:
    """Deterministic one-shot completion when no LLM is configured."""

    def _fn(ctx: dict[str, Any]) -> str:
        _ = ctx
        return json.dumps(
            {
                "reasoning": "Stub: mark goal complete (configure LLM for real browsing).",
                "action": {
                    "action": "wait",
                    "target": "",
                    "value": "0.01",
                    "confidence": 1,
                    "reason": "stub_terminal",
                },
                "goal_reached": True,
            },
        )

    return _fn


def run_web_agent_loop(
    page: Any,
    *,
    goal: str,
    ai_fn: Callable[[dict[str, Any]], str],
    max_steps: int = 40,
    max_duration_seconds: float = 300.0,
    max_ai_calls: int = 50,
    no_progress_streak: int = 3,
    no_op_streak_limit: int = 2,
    on_progress: Callable[[int, str], None] | None = None,
    on_after_step: Callable[[int], None] | None = None,
    approval_workflow: ApprovalWorkflow | None = None,
    approval_policy: ApprovalPolicy | None = None,
) -> WebAgentLoopResult:
    """
    T-024: combined DOM+PNG fingerprint for stall detection.
    T-025: ``max_duration_seconds`` wall clock (default 5 minutes).
    T-026: post-action no-op streak when state fingerprint unchanged (excluding ``wait``).
    T-053: ``max_ai_calls`` budget.
    T-055: optional ``on_after_step`` for checkpoint persistence.
    T-040: optional ``approval_policy`` merges automatic ``requires_approval`` flags.
    """
    policy = approval_policy if approval_policy is not None else get_default_approval_policy()

    t0 = time.monotonic()
    step = 0
    ai_calls = 0
    prev_fp: int | None = None
    same_fp_streak = 0
    no_op_streak = 0

    while step < max_steps:
        if time.monotonic() - t0 > max_duration_seconds:
            return WebAgentLoopResult(
                status="timeout",
                steps=step,
                ai_calls=ai_calls,
                detail="max_duration_seconds exceeded",
            )

        cap = capture_page_state(page)
        excerpt = str(cap.get("dom", ""))[:12_000]
        fp = state_fingerprint(cap)

        if prev_fp is not None and fp == prev_fp:
            same_fp_streak += 1
        else:
            same_fp_streak = 1
            prev_fp = fp

        if same_fp_streak >= no_progress_streak:
            return WebAgentLoopResult(
                status="no_progress",
                steps=step,
                ai_calls=ai_calls,
                detail="state_fingerprint_unchanged",
            )

        if ai_calls >= max_ai_calls:
            return WebAgentLoopResult(
                status="max_ai_calls",
                steps=step,
                ai_calls=ai_calls,
                detail="ai budget exhausted",
            )

        ctx = {
            "goal": goal,
            "step": step,
            "dom_excerpt": excerpt,
            "url": getattr(page, "url", "") or "",
        }

        ai_calls += 1
        try:
            parsed = with_validation_retries(
                lambda: ai_fn(ctx),
                max_attempts=2,
            )
        except ValidationFailedError as exc:
            log.warning("agent_loop_ai_invalid", error=str(exc))
            return WebAgentLoopResult(
                status="invalid_ai_response",
                steps=step,
                ai_calls=ai_calls,
                detail=str(exc),
            )

        action = parsed["action"]
        apply_policy_to_action(action, policy)
        if on_progress is not None:
            reason = action.get("reason", "")
            on_progress(step + 1, f"{action.get('action')}: {reason[:200]}")

        if action.get("requires_approval"):
            if approval_workflow is None:
                return WebAgentLoopResult(
                    status="approval_required_missing_channel",
                    steps=step,
                    ai_calls=ai_calls,
                    detail="requires_approval needs slack_channel_id on task payload",
                )
            approved = approval_workflow.request_approval_for_action(
                action=action,
                capture=cap,
            )
            if not approved:
                return WebAgentLoopResult(
                    status="failed",
                    steps=step,
                    ai_calls=ai_calls,
                    detail="approval_rejected",
                )

        fp_before = fp
        try:
            exec_res = execute_action_with_retry(page, action)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_loop_action_failed", step=step)
            return WebAgentLoopResult(
                status="failed",
                steps=step,
                ai_calls=ai_calls,
                detail=str(exc),
            )

        if not exec_res["ok"]:
            return WebAgentLoopResult(
                status="failed",
                steps=step,
                ai_calls=ai_calls,
                detail=exec_res.get("detail") or "action_not_ok",
            )

        cap_after = capture_page_state(page)
        fp_after = state_fingerprint(cap_after)
        kind = action.get("action", "")
        if kind != "wait" and fp_after == fp_before:
            no_op_streak += 1
        else:
            no_op_streak = 0

        if no_op_streak >= no_op_streak_limit:
            return WebAgentLoopResult(
                status="no_op",
                steps=step,
                ai_calls=ai_calls,
                detail="state_unchanged_after_action",
            )

        step += 1
        if on_after_step is not None:
            on_after_step(step)

        if parsed.get("goal_reached"):
            return WebAgentLoopResult(status="completed", steps=step, ai_calls=ai_calls)

    return WebAgentLoopResult(status="max_steps", steps=step, ai_calls=ai_calls)
