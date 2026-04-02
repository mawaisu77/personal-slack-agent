# Task Catalog — Personal AI Assistant Agent

**Source:** `docs/product-prd.md` v3.0 · **Epics:** `planning/epics.md`  
**Convention:** `T-XXX` = task ID. Linked epic in **Epic** column.

**Prioritization order (execution):** infrastructure & state → web loop → Slack interface → approval → voice → observability → testing/CI → production.

---

## Legend


| Complexity | Meaning              |
| ---------- | -------------------- |
| **S**      | ≤1–2 days            |
| **M**      | 3–5 days             |
| **L**      | >1 week or high risk |


---

## Foundation & Security (Phase 1)


| ID    | Epic    | Title                                | Description                                                                                                                                                                           | Inputs         | Outputs                           | Dependencies      | Acceptance Criteria                                                                      | Edge Cases                                      | C   |
| ----- | ------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | --------------------------------- | ----------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------- | --- |
| T-001 | E-STATE | DB schema: tasks & lifecycle         | Migrations for `tasks` with states: pending, running, waiting_for_approval, completed, failed, cancelled; timestamps; user_id; type; payload JSON; retry counts; cancellation reason. | PRD §3         | SQL migrations, ORM models        | —                 | All PRD states representable; cancelled from any state; migrations reversible documented | Concurrent updates to same task; partial writes | M   |
| T-002 | E-STATE | DB schema: checkpoints & resume      | Store per-step checkpoints for resume (PRD §15).                                                                                                                                      | PRD §15        | `checkpoints` table + FK task_id  | T-001             | Resume loads last valid checkpoint; idempotent writes                                    | Duplicate checkpoint sequence                   | M   |
| T-003 | E-QUEUE | Job schema & enqueue API             | Implement job payload matching PRD §4; validate `type` in `web|call`.                                                                                                                 | PRD job schema | Library + types                   | T-001             | Invalid payloads rejected at enqueue                                                     | Malformed JSON; oversized payload               | S   |
| T-004 | E-QUEUE | Redis queue consumer + FIFO/priority | FIFO with priority field; worker pop semantics documented.                                                                                                                            | Redis          | Worker loop abstraction           | T-003             | Ordering documented; priority affects dequeue                                            | Starvation of low priority                      | M   |
| T-005 | E-QUEUE | Retry + exponential backoff          | Retry policy on failure; configurable max attempts.                                                                                                                                   | PRD §4         | Retry middleware                  | T-004             | Backoff increases; attempts logged                                                       | Clock skew; poison message                      | M   |
| T-006 | E-QUEUE | Dead Letter Queue                    | Failed jobs after max retries to DLQ with reason.                                                                                                                                     | PRD §4         | DLQ topic/table + inspection path | T-005             | No infinite retry; DLQ queryable                                                         | DLQ flood                                       | S   |
| T-007 | E-ORCH  | Orchestrator enqueue & dispatch      | Accept new work from API/internal; push to queue; route by type.                                                                                                                      | T-003,T-004    | Dispatch service                  | T-001,T-003,T-004 | web/call jobs reach correct handler registration                                         | Unknown type dropped to error path              | M   |
| T-008 | E-ORCH  | Lifecycle API (internal)             | Valid transitions only; persist; emit events/logs.                                                                                                                                    | PRD §3         | State service API                 | T-001             | Illegal transition rejected with error code                                              | Race: two workers same task                     | M   |
| T-009 | E-ORCH  | Cancellation propagation             | User/system cancel: mark cancelled; signal worker cooperative stop.                                                                                                                   | PRD §3         | Cancel API + signals              | T-008             | Task ends cancelled; worker stops when safe                                              | Cancel during approval wait                     | M   |
| T-010 | E-SEC   | Secrets Manager wiring               | Load secrets from manager; no env plaintext for prod secrets.                                                                                                                         | PRD §13        | Config module                     | —                 | App fails fast if required secret missing                                                | Local dev override path documented              | S   |
| T-011 | E-SEC   | Encryption at rest plan              | Identify columns/blobs; KMS or DB encryption; migration plan.                                                                                                                         | PRD §13        | Doc + migrations                  | T-001,T-010       | Sensitive fields not plain in DB                                                         | Key rotation procedure stub                     | M   |
| T-012 | E-RUN   | Agent Runner process skeleton        | Long-running worker consuming queue; claims task; delegates to handlers.                                                                                                              | PRD §2.1       | Runner binary/service             | T-007,T-008       | Single task execution isolated in try/finally                                            | Worker crash mid-task                           | M   |
| T-013 | E-RUN   | Execution state store                | In-memory + persisted step index for loop.                                                                                                                                            | PRD §5         | State blob per run                | T-002,T-012       | Survives worker restart if checkpointed                                                  | Orphan execution                                | S   |
| T-014 | E-RUN   | AI client contract                   | Request/response validation; JSON schema for action; reasoning field.                                                                                                                 | PRD §5.2–6     | Client module                     | T-010             | Invalid AI output rejected; retry path                                                   | Malformed JSON from model                       | M   |
| T-015 | E-OBS   | Correlation & structured logging     | `task_id`, `user_id` on all service logs; JSON structure.                                                                                                                             | PRD §12        | Logger wrapper                    | —                 | grep by task_id works                                                                    | Log volume limits                               | S   |
| T-016 | E-SLACK | Slack app bootstrap (foundation)     | Verify signatures; health; minimal event ack path for <2s later.                                                                                                                      | PRD §16        | Slack app skeleton                | T-010             | Signature verification enforced                                                          | Replay attacks                                  | M   |


---

## Web Automation Core (Phase 2)


| ID    | Epic  | Title                      | Description                                                              | Inputs     | Outputs          | Dependencies            | Acceptance Criteria                     | Edge Cases                 | C   |
| ----- | ----- | -------------------------- | ------------------------------------------------------------------------ | ---------- | ---------------- | ----------------------- | --------------------------------------- | -------------------------- | --- |
| T-017 | E-WEB | Playwright session manager | Persistent profile dir; new browser context per task_id; cleanup on end. | PRD §7     | Session module   | T-015                   | No cross-task cookie leakage            | Disk full; profile corrupt | M   |
| T-018 | E-WEB | Capture: DOM + screenshot  | Serialize DOM subset + screenshot bytes; size limits.                    | PRD §5.1   | Capture API      | T-017                   | Captures available to AI step           | Huge DOM; screenshot fail  | M   |
| T-019 | E-WEB | Screenshot storage URLs    | Upload to S3/R2; return URL for logs/approval.                           | PRD §11–12 | Storage adapter  | T-010,T-018             | URLs stable for approval object         | Upload failure retry       | S   |
| T-020 | E-WEB | Action executor            | Implement click, type, scroll, wait, extract per schema.                 | PRD §5.2   | Executor         | T-017,T-018             | Each action returns success/fail struct | Stale selector; iframe     | L   |
| T-021 | E-WEB | Interaction retry (min 3)  | Retry failed interaction up to min 3 before bubbling.                    | PRD §7     | Retry wrapper    | T-020                   | Count logged                            | Infinite loop prevented    | S   |
| T-022 | E-WEB | Navigation validation      | After goto/nav, verify URL/DOM expectation when applicable.              | PRD §7     | Validator        | T-020                   | False navigations detected              | SPA soft nav               | M   |
| T-023 | E-RUN | Agent loop integration     | Wire capture→AI→execute→validate; loop until goal or stop.               | PRD §5.1   | Loop controller  | T-014,T-018,T-020,T-022 | Loop exits on success/fail/approval     | Partial AI response        | L   |
| T-024 | E-RUN | No-progress detection      | Track hash/signal of state; abort after 3 cycles no progress.            | PRD §5.1   | Progress tracker | T-023                   | Forced stop + log                       | Legitimate slow SPA        | M   |
| T-025 | E-RUN | Max duration 5 minutes     | Wall-clock guard on web run.                                             | PRD §5.1   | Timer            | T-023                   | Hard stop; state failed or checkpoint   | Clock jump                 | S   |
| T-026 | E-RUN | Validation layer (no-op)   | Detect no-op actions; trigger retry/fail per PRD §5.3.                   | PRD §5.3   | Validator        | T-020,T-023             | No silent no-ops                        | False positive no-op       | M   |
| T-027 | E-WEB | Error: screenshot + notify | On failure, capture screenshot, log, notify user channel hook.           | PRD §11    | Error pipeline   | T-019,T-023             | User sees actionable message            | Double failure             | S   |


---

## Voice Agent (Phase 3)


| ID    | Epic    | Title                         | Description                                               | Inputs | Outputs             | Dependencies      | Acceptance Criteria                       | Edge Cases                | C   |
| ----- | ------- | ----------------------------- | --------------------------------------------------------- | ------ | ------------------- | ----------------- | ----------------------------------------- | ------------------------- | --- |
| T-028 | E-VOICE | Provider abstraction          | Interface for Vapi/Bland/Retell; config-driven provider.  | PRD §9 | Interface + factory | T-010             | Swap provider without orchestrator change | Unsupported region        | M   |
| T-029 | E-VOICE | Outbound call execution       | Place call; handle real-time audio path per provider API. | PRD §9 | Call service        | T-028             | Call connects or fails with reason        | Busy; disconnect mid-call | L   |
| T-030 | E-VOICE | Number resolution hook        | Minimal resolver (manual number in payload or stub).      | PRD §9 | Resolver            | T-029             | Documented contract for future enrichment | Invalid E.164             | S   |
| T-031 | E-VOICE | Transcript + summary artifact | Store transcript; AI or provider summary; link to task.   | PRD §9 | Artifacts on task   | T-029             | Task record complete for success path     | Empty transcript          | M   |
| T-032 | E-RUN   | Route call jobs through Voice | Orchestrator dispatches `type=call` to voice pipeline.    | PRD §4 | Handler             | T-007,T-029,T-031 | End-to-end call task lifecycle            | Provider timeout          | M   |


---

## Slack + Approval (Phase 4)


| ID    | Epic    | Title                            | Description                                                | Inputs   | Outputs       | Dependencies      | Acceptance Criteria                         | Edge Cases            | C   |
| ----- | ------- | -------------------------------- | ---------------------------------------------------------- | -------- | ------------- | ----------------- | ------------------------------------------- | --------------------- | --- |
| T-033 | E-SLACK | `/do` command                    | Parse intent/payload; create web task; ack <2s.            | PRD §2.1 | Handler       | T-007,T-016,T-008 | Task created; user gets immediate ack       | Duplicate command     | M   |
| T-034 | E-SLACK | `/call` command                  | Create call task; ack <2s.                                 | PRD      | Handler       | T-032,T-033       | Same as above                               | Invalid phone         | M   |
| T-035 | E-SLACK | `/status`, `/cancel`, `/history` | Query state; cancel; list history per user.                | PRD      | Handlers      | T-008,T-009       | Consistent with DB                          | Pagination            | M   |
| T-036 | E-SLACK | Async updates for long tasks     | Post messages or update with progress.                     | PRD §16  | Notifier      | T-035             | User sees progress >30s tasks               | Rate limits           | M   |
| T-037 | E-APPR  | Approval persistence             | Table/API for approval object PRD §8.                      | PRD §8   | CRUD          | T-001             | All fields stored                           | Duplicate approval_id | S   |
| T-038 | E-APPR  | Block execution on approval      | Runner waits in `waiting_for_approval`; resume on approve. | PRD §8   | Gate in E-RUN | T-037,T-023       | Cannot commit irreversible without approved | Reject path           | L   |
| T-039 | E-APPR  | Slack interactive approve/reject | Buttons update approval; orchestrate resume.               | PRD §8   | UI handlers   | T-037,T-036       | Timeout path defined                        | Double-click approve  | M   |
| T-040 | E-APPR  | Approval triggers policy         | Payments, irreversible, uncertainty → require approval.    | PRD §8   | Policy module | T-038,T-020       | Configurable rules                          | Policy miss           | M   |
| T-041 | E-APPR  | Approval timeout                 | `expires_at` handling; task failure or safe abort.         | PRD §8   | Scheduler/job | T-037,T-039       | No indefinite wait                          | Timezone              | S   |


---

## Context, Observability, Security depth (Phase 5)


| ID    | Epic  | Title                       | Description                                   | Inputs    | Outputs           | Dependencies | Acceptance Criteria         | Edge Cases               | C   |
| ----- | ----- | --------------------------- | --------------------------------------------- | --------- | ----------------- | ------------ | --------------------------- | ------------------------ | --- |
| T-042 | E-CTX | Context schema & storage    | Structured user profile fields; encrypted.    | PRD §10   | Schema+migrations | T-011        | Minimal retrieval API       | Schema migration         | M   |
| T-043 | E-CTX | Masked retrieval for agents | Only allowed fields; mask in responses/logs.  | PRD §10   | Filter            | T-042,T-015  | No PII in logs from context | Field escalation request | M   |
| T-044 | E-OBS | AI I/O logging              | Log prompts/completions with redaction rules. | PRD §12   | Pipeline          | T-014,T-015  | PII/secrets masked          | Large payloads           | M   |
| T-045 | E-OBS | Replay / debug trace store  | Persist trace for replay tests.               | PRD §12   | Trace format      | T-044        | Replay harness can load     | Storage growth           | M   |
| T-046 | E-SEC | Audit log for approvals     | Immutable audit entries for approve/reject.   | PRD §8,13 | Audit table       | T-037        | Compliance query            | Tamper evidence          | S   |


---

## Testing & CI/CD (Phase 6)


| ID    | Epic   | Title                                   | Description                           | Inputs   | Outputs    | Dependencies | Acceptance Criteria            | Edge Cases         | C   |
| ----- | ------ | --------------------------------------- | ------------------------------------- | -------- | ---------- | ------------ | ------------------------------ | ------------------ | --- |
| T-047 | E-TEST | Unit tests: state machine               | All transitions + cancellation.       | PRD §3   | Test suite | T-008        | 100% transition matrix covered | —                  | M   |
| T-048 | E-TEST | Unit tests: validation & action parsing | AI output schema; action validation.  | PRD §5–6 | Tests      | T-014,T-026  | Golden tests for parser        | —                  | S   |
| T-049 | E-TEST | Integration: mock AI + browser          | Playwright against fixture; mock LLM. | PRD §14  | Tests      | T-023,T-020  | Stable in CI                   | Flaky timing       | L   |
| T-050 | E-TEST | Replay tests                            | Re-run trace; assert equivalence.     | PRD §14  | Tests      | T-045        | Documented scope               | Trace version skew | M   |
| T-051 | E-CICD | CI pipeline                             | Lint + unit + integration on PR.      | PRD §14  | YAML       | T-047–T-050  | Required checks green          | Secret in CI       | M   |
| T-052 | E-CICD | Build & deploy pipeline                 | Artifact build; staged deploy.        | PRD §14  | Pipeline   | T-051        | Rollback doc                   | Downtime           | M   |


---

## Production readiness (Phase 7)


| ID    | Epic    | Title                         | Description                                         | Inputs  | Outputs          | Dependencies      | Acceptance Criteria      | Edge Cases       | C   |
| ----- | ------- | ----------------------------- | --------------------------------------------------- | ------- | ---------------- | ----------------- | ------------------------ | ---------------- | --- |
| T-053 | E-ORCH  | Cost controls: AI call limits | Per-task cap on AI calls; enforce in loop.          | PRD §17 | Counter          | T-023             | Hard stop when exceeded  | Off-by-one       | S   |
| T-054 | E-ORCH  | Budget caps per user          | Daily/monthly limits; block or queue.               | PRD §17 | Quotas           | T-001,T-053       | User cannot exceed cap   | Reset boundary   | M   |
| T-055 | E-RUN   | Checkpoint integration        | Persist step checkpoints; resume from last valid.   | PRD §15 | Integration      | T-002,T-023       | Resume after worker kill | Duplicate resume | M   |
| T-056 | E-SLACK | Load test: ack <2s            | Measure p95 ack under concurrent commands.          | PRD §16 | Report           | T-033–T-035       | Meets target in staging  | Cold start       | M   |
| T-057 | E-ORCH  | Concurrent tasks scale        | Horizontal workers; no shared mutable global state. | PRD §16 | Doc              | T-012,T-004       | Safe concurrency         | Hot partitions   | M   |
| T-058 | Release | Runbooks & on-call            | Deploy, rollback, DLQ replay, incident checklist.   | PRD §18 | `docs/runbooks/` | T-006,T-051       | Operator can execute     | —                | S   |
| T-059 | Release | Acceptance demo script        | E2E: web + approval + logging + recovery.           | PRD §18 | Script           | T-038,T-055,T-045 | Passes in staging        | —                | M   |


---

## Task index (quick lookup)


| ID    | Title                            |
| ----- | -------------------------------- |
| T-001 | DB schema: tasks & lifecycle     |
| T-002 | DB schema: checkpoints & resume  |
| T-003 | Job schema & enqueue API         |
| T-004 | Redis queue + FIFO/priority      |
| T-005 | Retry + exponential backoff      |
| T-006 | Dead Letter Queue                |
| T-007 | Orchestrator enqueue & dispatch  |
| T-008 | Lifecycle API                    |
| T-009 | Cancellation propagation         |
| T-010 | Secrets Manager wiring           |
| T-011 | Encryption at rest plan          |
| T-012 | Agent Runner skeleton            |
| T-013 | Execution state store            |
| T-014 | AI client contract               |
| T-015 | Correlation & structured logging |
| T-016 | Slack app bootstrap              |
| T-017 | Playwright session manager       |
| T-018 | Capture DOM + screenshot         |
| T-019 | Screenshot storage URLs          |
| T-020 | Action executor                  |
| T-021 | Interaction retry (min 3)        |
| T-022 | Navigation validation            |
| T-023 | Agent loop integration           |
| T-024 | No-progress detection            |
| T-025 | Max duration 5 minutes           |
| T-026 | Validation layer (no-op)         |
| T-027 | Error screenshot + notify        |
| T-028 | Voice provider abstraction       |
| T-029 | Outbound call execution          |
| T-030 | Number resolution hook           |
| T-031 | Transcript + summary             |
| T-032 | Route call jobs                  |
| T-033 | `/do` command                    |
| T-034 | `/call` command                  |
| T-035 | `/status`, `/cancel`, `/history` |
| T-036 | Async updates                    |
| T-037 | Approval persistence             |
| T-038 | Block execution on approval      |
| T-039 | Slack interactive approve/reject |
| T-040 | Approval triggers policy         |
| T-041 | Approval timeout                 |
| T-042 | Context schema & storage         |
| T-043 | Masked retrieval                 |
| T-044 | AI I/O logging                   |
| T-045 | Replay trace store               |
| T-046 | Audit log approvals              |
| T-047 | Unit tests: state machine        |
| T-048 | Unit tests: validation           |
| T-049 | Integration mock AI+browser      |
| T-050 | Replay tests                     |
| T-051 | CI pipeline                      |
| T-052 | Build & deploy pipeline          |
| T-053 | Cost: AI call limits             |
| T-054 | Budget caps per user             |
| T-055 | Checkpoint integration           |
| T-056 | Load test ack                    |
| T-057 | Concurrent tasks scale           |
| T-058 | Runbooks                         |
| T-059 | Acceptance demo                  |


