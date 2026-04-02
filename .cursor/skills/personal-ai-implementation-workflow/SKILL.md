---
name: personal-ai-implementation-workflow
description: Guides end-to-end implementation from an approved plan to working code for the Personal AI Assistant. Use when starting a new feature, breaking a plan into deliverables, scaffolding services, or when the user asks how to implement, ship, or structure incremental work.
---

# Implementation workflow

## Preconditions

- Have an **approved Planner output** or a **written mini-spec** (scope, modules, acceptance criteria). If missing, stop and get alignment before large edits.

## Sequence

1. **Scaffold** — Create packages and empty modules that match the design; add `__init__.py` where needed; wire FastAPI app and routers without business logic first.
2. **Data layer** — Migrations/models for task state and any new entities; verify `pending` → `running` → `waiting_for_approval` → terminal states are representable.
3. **Core logic** — Orchestrator + state transitions; then agents (web/voice) behind interfaces; then Slack/adapters.
4. **Cross-cutting** — Logging context (task/user IDs), retries, approval gates on irreversible actions.
5. **Verify locally** — Run app/tests; exercise happy path plus failure paths (timeout, rejection, cancel).
6. **Verifier pass** — Use **personal-ai-verifier** (or equivalent QA) for scenarios, bugs, and risk before **personal-ai-reviewer**.

## Deliverable shape

- **Folder structure** stated up front for any non-trivial change.
- **Incremental commits**: prefer small, reviewable steps over one huge diff.
- **Setup**: list env vars, services (Postgres, Redis), and commands to run migrations and the API.

## Anti-patterns

- Implementing Slack handlers before task state exists (leads to fake “done”).
- Hard-coding approval bypasses for convenience.
- Monolithic files that mix orchestration, HTTP, and Playwright in one module.

## Handoff

- After implementation, summarize **assumptions**, **known gaps**, and **how to test** for **Verifier** first, then **Reviewer** for final audit (**Approve / Reject / Changes required**).
