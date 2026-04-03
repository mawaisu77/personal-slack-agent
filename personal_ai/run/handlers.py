"""Worker dispatch handlers (T-012, T-023, T-032, Batch 8)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from personal_ai.config.settings import get_settings
from personal_ai.db.session import session_scope
from personal_ai.orchestrator.dispatch import OrchestratorDispatchService
from personal_ai.queue.schemas import JobPayload
from personal_ai.run.agent_loop import default_stub_ai_fn, run_web_agent_loop
from personal_ai.run.approval_workflow import ApprovalWorkflow
from personal_ai.slack_interface.progress import SlackProgressNotifier, post_task_terminal_note
from personal_ai.state.checkpoint_store import CheckpointStore
from personal_ai.voice.artifacts import merge_voice_artifacts
from personal_ai.voice.factory import get_voice_provider
from personal_ai.voice.outbound import OutboundCallService
from personal_ai.voice.phone import resolve_phone_e164


def web_agent_stub(job: JobPayload) -> dict[str, Any]:
    """
    Web task handler: ``AGENT_WEB_MODE=stub`` (default) for fast tests; ``loop`` runs T-023.
    """
    settings = get_settings()
    if settings.agent_web_mode == "stub":
        return {"handler": "web_stub", "task_id": str(job.task_id), "ok": True}

    with session_scope() as session:
        return _web_agent_loop_with_db(session, job)


def _web_agent_loop_with_db(session: Session, job: JobPayload) -> dict[str, Any]:
    from personal_ai.web.error_pipeline import notify_web_task_error
    from personal_ai.web.session_manager import PlaywrightSessionManager

    settings = get_settings()
    goal = (job.payload.get("goal") or "").strip()
    raw_ch = job.payload.get("slack_channel_id")
    slack_channel_id = raw_ch.strip() if isinstance(raw_ch, str) else None
    notifier: SlackProgressNotifier | None = None
    if slack_channel_id:
        notifier = SlackProgressNotifier(
            user_id=job.user_id,
            channel_id=slack_channel_id,
            task_id=job.task_id,
        )

    def on_progress(step: int, msg: str) -> None:
        if notifier is not None:
            notifier.maybe_post(step, msg)

    approval_workflow: ApprovalWorkflow | None = None
    if slack_channel_id:
        approval_workflow = ApprovalWorkflow(
            session,
            task_id=job.task_id,
            user_id=job.user_id,
            slack_channel_id=slack_channel_id,
        )

    def on_after_step(step_idx: int) -> None:
        n = settings.agent_checkpoint_every_n_steps
        if n <= 0 or step_idx % n != 0:
            return
        cs = CheckpointStore(session)
        cs.append_checkpoint(
            job.task_id,
            {"step": step_idx, "goal": goal, "kind": "web_agent_loop"},
        )
        session.flush()

    mgr = PlaywrightSessionManager()
    tid = str(job.task_id)
    mgr.start()
    ctx = mgr.new_context_for_task(tid)
    page = ctx.new_page()
    try:
        start_url = (job.payload.get("start_url") or "about:blank").strip() or "about:blank"
        page.goto(start_url, timeout=60_000)
        try:
            result = run_web_agent_loop(
                page,
                goal=goal,
                ai_fn=default_stub_ai_fn(goal),
                max_steps=settings.agent_max_steps,
                max_duration_seconds=settings.agent_max_duration_seconds,
                max_ai_calls=settings.agent_max_ai_calls,
                no_op_streak_limit=settings.agent_no_op_streak_limit,
                on_progress=on_progress,
                on_after_step=on_after_step,
                approval_workflow=approval_workflow,
            )
        except Exception as exc:  # noqa: BLE001
            notify_web_task_error(job, exc, page=page)
            raise

        summary = f"status={result.status} steps={result.steps} ai_calls={result.ai_calls}"
        if slack_channel_id is not None:
            post_task_terminal_note(
                user_id=job.user_id,
                channel_id=slack_channel_id,
                task_id=job.task_id,
                summary=summary,
            )
        if result.status != "completed":
            msg = f"web_agent_loop:{result.status}:{result.detail}"
            raise RuntimeError(msg)
        return {
            "handler": "web_agent",
            "task_id": str(job.task_id),
            "ok": True,
            "loop_status": result.status,
            "steps": result.steps,
            "ai_calls": result.ai_calls,
        }
    finally:
        mgr.close_context_for_task(tid)


def call_agent_stub(job: JobPayload) -> dict[str, Any]:
    """
    Minimal call path: resolve number, place call; attach transcript/summary stubs (T-031).
    """
    phone = resolve_phone_e164(job.payload)
    provider = get_voice_provider()
    svc = OutboundCallService(provider)
    res = svc.place_call(phone, metadata={"task_id": str(job.task_id)})
    merged = merge_voice_artifacts(
        job.payload,
        transcript="(placeholder transcript)",
        summary="(placeholder summary)",
        call_id=res.call_id,
    )
    return {
        "handler": "call_stub",
        "task_id": str(job.task_id),
        "phone_e164": phone,
        "call_id": res.call_id,
        "success": res.success,
        "reason": res.reason,
        "payload_patch": merged,
    }


def register_default_handlers(svc: OrchestratorDispatchService) -> None:
    """Wire stub handlers for queue worker dispatch."""
    svc.register_handler("web", web_agent_stub)
    svc.register_handler("call", call_agent_stub)
