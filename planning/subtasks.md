# Subtasks — Ordered Implementation Steps

**Companion:** `planning/tasks.md` · Each subtask is actionable, ordered, and tagged with **Module** (service/package).

**Module tags:** `STATE` · `QUEUE` · `ORCH` · `RUN` · `WEB` · `VOICE` · `SLACK` · `APPR` · `CTX` · `OBS` · `SEC` · `INFRA`

---

## T-001 — DB schema: tasks & lifecycle

1. [STATE] Define SQLAlchemy/Pydantic models for `tasks` with enum matching PRD states + `cancelled`.
2. [STATE] Add migration (Alembic/Flyway equivalent); indexes on `user_id`, `status`, `created_at`.
3. [STATE] Add DB constraint: valid state enum only.
4. [OBS] Log migration version on deploy.

## T-002 — Checkpoints

1. [STATE] Create `checkpoints` table: `task_id`, `sequence`, `payload_json`, `created_at`.
2. [STATE] API: `append_checkpoint`, `latest_checkpoint(task_id)`.
3. [ORCH] Document resume contract with E-RUN.

## T-003 — Job schema

1. [QUEUE] Define Pydantic `JobPayload` with `task_id`, `user_id`, `type`, `payload`, `priority`, `retries`.
2. [QUEUE] Serialize/deserialize to Redis message body; size limit enforced.

## T-004 — Redis queue

1. [QUEUE] Implement consumer interface `dequeue()` blocking with timeout.
2. [QUEUE] Priority queue semantics (document algorithm: e.g. sorted sets).
3. [INFRA] Docker compose or local Redis for dev.

## T-005 — Retry + backoff

1. [QUEUE] Wrap handler with retry; exponential backoff formula in config.
2. [OBS] Log attempt count per job.

## T-006 — DLQ

1. [QUEUE] On max retries, publish to DLQ with `last_error`, `task_id`.
2. [INFRA] CLI or admin endpoint to list DLQ entries.

## T-007 — Orchestrator dispatch

1. [ORCH] HTTP/internal API: `submit_task` creates DB row `pending`, enqueues job.
2. [ORCH] Worker registry: `web` → WebAgentHandler, `call` → VoiceAgentHandler stubs.

## T-008 — Lifecycle API

1. [STATE] Implement `transition(task_id, from_states, to_state)` with row lock.
2. [STATE] Return error if transition illegal.
3. [OBS] Audit log line on each transition.

## T-009 — Cancellation

1. [ORCH] `cancel_task` sets `cancel_requested_at`; state → `cancelled` when worker acknowledges.
2. [RUN] Runner checks cancel flag between loop iterations.

## T-010 — Secrets Manager

1. [SEC] Config loader: `get_secret(name)` from env vs AWS SM.
2. [INFRA] Document local `.env.example` without real secrets.

## T-011 — Encryption at rest

1. [SEC] List columns: tokens, PII blobs.
2. [STATE] Migration: encrypt columns using KMS envelope or pgcrypto (document choice).

## T-012 — Agent Runner skeleton

1. [RUN] Main loop: dequeue → load task → run handler → finalize state.
2. [RUN] Global exception handler → `failed` + log.

## T-013 — Execution state store

1. [RUN] In-memory dict keyed by `run_id` + periodic flush to `checkpoints`.

## T-014 — AI client contract

1. [RUN] Define JSON schema for AI response; validate with `jsonschema`.
2. [RUN] Retry on validation failure (bounded).

## T-015 — Structured logging

1. [OBS] Middleware/contextvar for `task_id`, `user_id` on every log line.

## T-016 — Slack bootstrap

1. [SLACK] Bolt app init; `/health` slash or HTTP health.
2. [SLACK] Verify Slack signing secret on every request.

## T-017 — Playwright session manager

1. [WEB] Launch browser with `userDataDir` per deployment; `newContext()` per `task_id`.
2. [WEB] `finally`: close context; optional retain profile policy.

## T-018 — Capture

1. [WEB] `page.content()` or accessibility snapshot per PRD choice; screenshot PNG.
2. [WEB] Truncate DOM string if over limit; log warning.

## T-019 — Screenshot storage

1. [WEB] Upload bytes; return HTTPS URL; store URL on task step log.

## T-020 — Action executor

1. [WEB] Map `action` enum to Playwright calls; locator from `target`.
2. [WEB] Return `{success, detail}` for validation layer.

## T-021 — Interaction retry

1. [WEB] Wrap executor with `for attempt in range(3):`.

## T-022 — Navigation validation

1. [WEB] After `goto`, assert URL pattern if goal requires.

## T-023 — Agent loop integration

1. [RUN] `while not done:` capture → build prompt → `ai_client` → parse action → `execute` → `validate`.
2. [RUN] Integrate T-024, T-025, T-053 counters.

## T-024 — No-progress

1. [RUN] Hash fingerprint of DOM/screenshot; if unchanged 3 iterations → break.

## T-025 — Max duration

1. [RUN] `asyncio.wait_for` or monotonic deadline at loop start.

## T-026 — No-op validation

1. [RUN] Compare pre/post fingerprint; if identical after action → retry or escalate.

## T-027 — Error pipeline

1. [WEB] On exception: screenshot → `notify_user(task_id, error, url)`.
2. [SLACK] Stub notifier → replace in T-036.

## T-028 — Voice abstraction

1. [VOICE] `VoiceProvider` ABC: `start_call`, `end_call`, `on_event`.

## T-029 — Outbound call

1. [VOICE] Implement one provider (e.g. Vapi) with API keys from secrets.

## T-030 — Number resolution

1. [VOICE] Read `payload.phone_e164` from job; validate format.

## T-031 — Transcript + summary

1. [VOICE] On call end: fetch transcript; optional LLM summary via E-RUN AI client.

## T-032 — Route call jobs

1. [ORCH] Register handler calling T-029–T-031; set task `completed`/`failed`.

## T-033 — `/do`

1. [SLACK] Parse text payload; call `submit_task(type=web)`.
2. [SLACK] Immediate ephemeral or channel ack &lt;2s.

## T-034 — `/call`

1. [SLACK] Same with `type=call` + phone validation.

## T-035 — status/cancel/history

1. [SLACK] Map to `GET task`, `cancel_task`, `list_tasks(user)`.

## T-036 — Async updates

1. [SLACK] Background worker posts thread updates on state changes (webhook or polling).

## T-037 — Approval persistence

1. [APPR] Table `approvals` matching PRD §8 object.
2. [APPR] Unique `approval_id` (UUID).

## T-038 — Block execution

1. [RUN] Before irreversible browser action: call `request_approval()` → pause → poll DB until resolved.
2. [STATE] Set `waiting_for_approval`.

## T-039 — Slack buttons

1. [SLACK] Block Kit message with Approve/Reject; interaction endpoint updates `approvals`.
2. [APPR] Signal runner (Redis pub/sub or DB poll) to resume.

## T-040 — Triggers policy

1. [APPR] Config YAML: which action types require approval (payment, submit, etc.).

## T-041 — Timeout

1. [APPR] Cron/worker: expire pending approvals → task `failed` with reason `approval_timeout`.

## T-042 — Context schema

1. [CTX] Tables for user profile fragments; encrypt at application layer or DB.

## T-043 — Masked retrieval

1. [CTX] `get_context(user_id, fields=[...])` returns only allowed keys.
2. [OBS] Redact in `log_context_access`.

## T-044 — AI I/O logging

1. [OBS] Persist prompt/response hashes + truncated content in trace store.

## T-045 — Replay store

1. [OBS] JSON lines per step; version field for replay tests.

## T-046 — Audit log

1. [APPR] Append-only `approval_audit` with actor, timestamp, decision.

## T-047 — Unit tests state

1. [TEST] Parameterized tests for every `(from,to)` allowed transition.

## T-048 — Unit tests validation

1. [TEST] Golden files for AI JSON samples: valid/invalid.

## T-049 — Integration

1. [TEST] Playwright against `static/fixtures/page.html`; mock OpenAI/Claude HTTP.

## T-050 — Replay tests

1. [TEST] Load trace from T-045; assert runner decisions match.

## T-051 — CI

1. [CICD] GitHub Actions / equivalent: `ruff`, `pytest`, `mypy` optional.

## T-052 — Deploy

1. [CICD] Build container; push; deploy to staging with secrets from SM.

## T-053 — AI call limits

1. [RUN] Increment counter per AI round; break loop when `>= limit`.

## T-054 — Budget caps

1. [ORCH] Check user quota before `submit_task`; return 429-style message to Slack.

## T-055 — Checkpoint integration

1. [RUN] After each successful step, `append_checkpoint`.

## T-056 — Load test ack

1. [INFRA] k6 or Locust hitting Slack interactivity mock; measure p95.

## T-057 — Concurrency

1. [ORCH] Document horizontal scaling; idempotent handlers.

## T-058 — Runbooks

1. [DOC] Markdown: deploy, rollback, DLQ drain.

## T-059 — Acceptance demo

1. [DOC] Scripted walkthrough checklist tied to PRD §18.
