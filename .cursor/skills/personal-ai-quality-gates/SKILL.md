---
name: personal-ai-quality-gates
description: Defines quality checks before merge or release for the Personal AI Assistant codebase. Use when finishing a task, before opening a PR, when the user asks for a pre-merge checklist, or when hardening error paths, tests, and observability.
---

# Quality gates

## Four-role pipeline

Default order: **Planner → Executor → Verifier → Reviewer**. If Verifier finds issues, **Executor fixes** and work returns to **Verifier** before a final **Reviewer** sign-off.

## Before considering work “done”

- [ ] **State model**: Task transitions are consistent; no illegal jumps; persistence matches design.
- [ ] **HITL**: Irreversible actions require `waiting_for_approval` (or equivalent) and cannot complete without an explicit approval record.
- [ ] **Secrets**: No new literals; env/secret manager only; logs do not print tokens or raw PII.
- [ ] **External I/O**: Timeouts on HTTP/SDK calls; retries with backoff where safe; stuck detection where designed; clear user-facing errors.
- [ ] **Web failures**: Screenshot/diagnostic hooks when applicable.
- [ ] **Observability**: Logs include task/correlation identifiers for the main paths you added.

## Tests (proportionate)

- Unit-test **pure logic** (state machines, parsing, policy).
- Integration tests for **critical paths** when test harness exists (e.g. API + DB); skip heavy E2E unless requested.

## Slack and async UX

- Long tasks: progress or heartbeat consistent with project rules; slash commands registered and documented if new.

## Quick self-review

- Imports and names match existing conventions.
- No dead code or commented-out secrets left behind.
- `README` or `docs/` updated only if behavior or setup changed (follow repo doc norms).

Use **personal-ai-verifier** for test scenarios and defect lists; use **personal-ai-reviewer** for holistic production approval after Verifier is satisfied (or when explicitly requested).

Before claiming “done” or opening a PR, apply **verification-before-completion** (run the real commands; evidence before claims).

For large features, prefer **writing-implementation-plans** → **executing-written-plans** (or **subagent-task-batches** when tasks are independent).
