# Agent Validation Scenarios

**Source:** `docs/product-prd.md` (flows, lifecycle, approval, errors) · **Purpose:** End-to-end validation for AI-assisted execution—not a substitute for automated tests in `planning/test-plan.md`.

Each scenario: **Input**, **Expected behavior**, **Failure conditions**.

---

## Scenario A: `/do` — web order / checkout flow (requires approval)

**Maps to:** PRD §3, §5–8, §11; tasks T-023, T-038–T-040, T-033.

| Field | Description |
|--------|-------------|
| **Input** | User `/do` with natural language goal: “Order replacement filter from example.com cart; use saved address.” Task payload includes `user_id`, goal text, optional URL hints. Context store returns minimal shipping fields (masked in logs). |
| **Expected behavior** | Slack ack &lt;2s. Task `pending`→`running`. Agent loop: capture DOM+screenshot → AI structured action → execute → validate. Before payment/submit, policy triggers approval: task `waiting_for_approval`; Slack message includes `action_summary`, `screenshot_url`, Approve/Reject. On Approve within `expires_at`, execution resumes; on success task `completed`. Logs contain each action, AI JSON (redacted), screenshot refs. |
| **Failure conditions** | AI returns invalid JSON → retry bounded; element not found after 3 interaction retries → screenshot + `failed`. No progress 3 cycles → stop per PRD §5.1. Duration &gt;5min → stop. Approval timeout → task `failed` with reason. User Reject → task `failed` or `cancelled` per policy. Cancel during run → `cancelled`. DLQ if worker dies after max retries. |

---

## Scenario B: `/call` — booking / reservation flow

**Maps to:** PRD §9, §4; tasks T-032–T-034, T-029–T-031.

| Field | Description |
|--------|-------------|
| **Input** | User `/call` with goal: “Call restaurant X to book table Saturday 7pm”; payload includes E.164 number or resolution fields per T-030. |
| **Expected behavior** | Ack &lt;2s. Job `type=call`. Voice provider places call; real-time conversation handled; on completion transcript + summary stored on task; task `completed`. Correlation logs across voice + orchestrator. |
| **Failure conditions** | Invalid number format → task `failed` before dial. Provider error / busy / hangup → `failed` with reason; partial transcript saved if policy allows. Cancellation → `cancelled`. AI/voice budget exceeded → `failed` per T-053/T-054. |

---

## Scenario C: Form filling (non-payment) with uncertainty approval

**Maps to:** PRD §8 (uncertainty trigger); tasks T-040, T-026.

| Field | Description |
|--------|-------------|
| **Input** | `/do` goal: “Submit contact form” on fixture site; AI reports low `confidence` on mandatory field mapping. |
| **Expected behavior** | Policy treats low confidence as approval trigger; user receives summary + screenshot; execution blocked until decision. After approve, run completes or fails on validation. |
| **Failure conditions** | If approval bypassed (bug) → **validation failure for release**. Timeout on approval → `failed`. |

---

## Scenario D: Error recovery — transient site failure

**Maps to:** PRD §11, §15; tasks T-005, T-021, T-027, T-055.

| Field | Description |
|--------|-------------|
| **Input** | Simulated 503 or network drop mid-loop; then recovery. |
| **Expected behavior** | Interaction retries exhaust with backoff; screenshot + user notify; if checkpoint exists, resume from last valid checkpoint on manual or automatic retry task per product policy. Logs show retry counts and errors. |
| **Failure conditions** | Infinite retry (bug). Lost checkpoint → cannot resume. Secrets in error message (must never happen). |

---

## Scenario E: `/status` / `/history` / `/cancel`

**Maps to:** PRD §3; tasks T-035, T-009.

| Field | Description |
|--------|-------------|
| **Input** | `/status` for active `task_id`; `/history` lists recent tasks; `/cancel` on `running` task. |
| **Expected behavior** | Status reflects DB truth only. History paginated and scoped to user. Cancel transitions to `cancelled` and worker stops when safe. |
| **Failure conditions** | Stale Slack UI vs DB (document eventual consistency); cancel after terminal → clear error. |

---

## Scenario F: Queue DLQ and operator recovery

**Maps to:** PRD §4; tasks T-006, T-058.

| Field | Description |
|--------|-------------|
| **Input** | Poison job always throws in handler. |
| **Expected behavior** | After max retries job in DLQ with error; operator can inspect; runbook describes replay after fix. |
| **Failure conditions** | Silent drop; duplicate replay causing double side effects without idempotency (document idempotency keys). |

---

## Scenario G: Replay / debug trace (observability)

**Maps to:** PRD §12; tasks T-044, T-045, T-050.

| Field | Description |
|--------|-------------|
| **Input** | Completed task with stored trace; replay test harness loads trace. |
| **Expected behavior** | Replay validates decisions or outputs match recorded expectations (scope per test design). Debug UI or CLI can list steps. |
| **Failure conditions** | PII in trace in non-secure environment; trace version mismatch without migration. |

---

## Scenario H: Security — secrets and masking

**Maps to:** PRD §13, §10; tasks T-010, T-043, T-044.

| Field | Description |
|--------|-------------|
| **Input** | Task loads context with API token; AI prompt includes sensitive hint. |
| **Expected behavior** | Secrets only from SM; logs and Slack show masked values; context retrieval minimal fields. |
| **Failure conditions** | Plaintext secret in repo, log, or Slack payload → **block release**. |

---

## Sign-off checklist (manual)

- [ ] Scenarios A–H exercised in staging with evidence (screenshots/log excerpts).
- [ ] PRD §18 acceptance: E2E execution, approval enforced, full logging, recovery demonstrated.
- [ ] `planning/dependencies.json` respected: no task started before dependencies complete.
