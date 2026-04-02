# Test Plan — By Task

**Source:** `docs/product-prd.md` §14 · **Tasks:** `planning/tasks.md`

For each task: **Unit**, **Integration**, **Simulation**, **Failure cases**. Logging: every task should have tests or checks that prove observability hooks exist where specified.

---

## T-001 — DB schema: tasks

| Type | Required |
|------|----------|
| Unit | Enum covers all PRD states including `cancelled`; model validators |
| Integration | Migration up/down on clean DB; concurrent insert two tasks |
| Simulation | N/A |
| Failure | Invalid state string rejected at ORM boundary |

---

## T-002 — Checkpoints

| Type | Required |
|------|----------|
| Unit | Sequence monotonic; duplicate sequence rejected |
| Integration | FK cascade behavior; large payload boundary |
| Simulation | Resume reader picks latest |
| Failure | Missing task_id → FK error |

---

## T-003 — Job schema

| Type | Required |
|------|----------|
| Unit | Pydantic rejects wrong `type`; missing `task_id` |
| Integration | Round-trip serialize to Redis mock |
| Simulation | N/A |
| Failure | Oversized payload rejected |

---

## T-004 — Redis queue

| Type | Required |
|------|----------|
| Unit | Priority ordering deterministic (documented fixture) |
| Integration | Consumer receives jobs in expected order |
| Simulation | Multi-worker no duplicate delivery (if exactly-once not guaranteed, document at-least-once) |
| Failure | Redis down → connection error surfaced |

---

## T-005 — Retry + backoff

| Type | Required |
|------|----------|
| Unit | Backoff timing formula with mocked clock |
| Integration | Handler fails twice then succeeds → 2 retries logged |
| Simulation | N/A |
| Failure | Max attempts → propagate to DLQ path |

---

## T-006 — DLQ

| Type | Required |
|------|----------|
| Unit | DLQ message contains `last_error` |
| Integration | End-to-end poison job lands in DLQ |
| Simulation | Operator list command returns entry |
| Failure | DLQ storage full / permission |

---

## T-007 — Orchestrator dispatch

| Type | Required |
|------|----------|
| Unit | Router maps `web`/`call` to correct handler id |
| Integration | Submit creates `pending` + visible job |
| Simulation | N/A |
| Failure | DB write ok but enqueue fails → compensating transaction or reconciler |

---

## T-008 — Lifecycle API

| Type | Required |
|------|----------|
| Unit | Matrix: all illegal transitions raise |
| Integration | Two concurrent transitions: one wins, one fails |
| Simulation | N/A |
| Failure | Stale `from_state` optimistic lock |

---

## T-009 — Cancellation

| Type | Required |
|------|----------|
| Unit | Cancel from `running` vs `waiting_for_approval` |
| Integration | Runner observes cancel flag within N seconds |
| Simulation | User cancels long web task |
| Failure | Cancel after already `completed` → no-op/error per spec |

---

## T-010 — Secrets Manager

| Type | Required |
|------|----------|
| Unit | Mock SM returns secret; missing key raises at startup |
| Integration | Local dev path uses env only |
| Simulation | N/A |
| Failure | SM throttling / network |

---

## T-011 — Encryption at rest

| Type | Required |
|------|----------|
| Unit | Round-trip encrypt/decrypt test vector |
| Integration | Migration encrypts existing rows |
| Simulation | N/A |
| Failure | Wrong KMS key |

---

## T-012 — Agent Runner skeleton

| Type | Required |
|------|----------|
| Unit | Handler exception → task `failed` |
| Integration | Fake queue job runs end-to-end |
| Simulation | Worker kill mid-task → task recoverable via checkpoint (with T-055) |
| Failure | Handler timeout |

---

## T-013 — Execution state store

| Type | Required |
|------|----------|
| Unit | Merge checkpoint with in-memory state |
| Integration | Restart worker reloads from DB |
| Simulation | N/A |
| Failure | Corrupt checkpoint JSON |

---

## T-014 — AI client contract

| Type | Required |
|------|----------|
| Unit | Valid/invalid JSON samples |
| Integration | Mock HTTP AI returns bad JSON → retry |
| Simulation | N/A |
| Failure | Rate limit from AI provider |

---

## T-015 — Structured logging

| Type | Required |
|------|----------|
| Unit | Log record contains `task_id` when context set |
| Integration | Request without context does not crash |
| Simulation | grep log file by task_id in fixture |
| Failure | Missing context → explicit “unknown” tag |

---

## T-016 — Slack bootstrap

| Type | Required |
|------|----------|
| Unit | Invalid signature rejected 401 |
| Integration | Valid signed request passes |
| Simulation | N/A |
| Failure | Wrong signing secret |

---

## T-017 — Playwright session manager

| Type | Required |
|------|----------|
| Unit | N/A (browser) |
| Integration | Two tasks two contexts no shared cookies |
| Simulation | Open page set cookie; other context empty |
| Failure | Profile directory not writable |

---

## T-018 — Capture

| Type | Required |
|------|----------|
| Integration | Screenshot non-empty PNG; DOM string length cap |
| Simulation | Huge page truncation logged |
| Failure | Page closed mid-capture |

---

## T-019 — Screenshot storage

| Type | Required |
|------|----------|
| Unit | Mock S3 put/get URL |
| Integration | Upload failure retries |
| Simulation | N/A |
| Failure | Invalid credentials |

---

## T-020 — Action executor

| Type | Required |
|------|----------|
| Unit | Pure mapping tests with mocked page |
| Integration | Each action type against fixture HTML |
| Simulation | Wrong selector → structured failure |
| Failure | Timeout on click |

---

## T-021 — Interaction retry

| Type | Required |
|------|----------|
| Unit | Stops at 3 attempts |
| Integration | Flaky click succeeds on 3rd |
| Failure | All attempts fail → bubble |

---

## T-022 — Navigation validation

| Type | Required |
|------|----------|
| Integration | Wrong URL after nav triggers failure path |
| Failure | SPA same URL different content (document limitation) |

---

## T-023 — Agent loop integration

| Type | Required |
|------|----------|
| Integration | Mock AI returns sequence of actions → task completes |
| Simulation | Full loop with fixture page |
| Failure | AI returns invalid action repeatedly |

---

## T-024 — No-progress

| Type | Required |
|------|----------|
| Unit | Same fingerprint 3x triggers exit |
| Integration | Loop stops; task `failed` with reason |
| Failure | Hash collision unlikely — document |

---

## T-025 — Max duration

| Type | Required |
|------|----------|
| Unit | Timer fires at 5m with fake clock |
| Integration | Long-running step killed |
| Failure | System sleep / clock skew |

---

## T-026 — No-op validation

| Type | Required |
|------|----------|
| Unit | Identical before/after → retry path |
| Integration | With T-020 |
| Failure | False positive rate documented |

---

## T-027 — Error pipeline

| Type | Required |
|------|----------|
| Integration | Exception yields screenshot URL in log |
| Failure | Notifier down → log only |

---

## T-028–T-031 — Voice

| Type | Required |
|------|----------|
| Unit | Provider mock implements ABC |
| Integration | Sandbox call or recorded API mock |
| Simulation | Full call task success and busy signal |
| Failure | Provider 500; dropped call |

---

## T-032 — Route call jobs

| Type | Required |
|------|----------|
| Integration | Enqueue call job → voice handler invoked |
| Failure | Provider misconfig |

---

## T-033–T-036 — Slack commands

| Type | Required |
|------|----------|
| Unit | Slash command parsers |
| Integration | Slack signature + command creates task |
| Simulation | `/cancel` mid-run |
| Failure | Slack API rate limit |

---

## T-037–T-041 — Approval

| Type | Required |
|------|----------|
| Unit | State machine for approval `pending→approved|rejected|expired` |
| Integration | Block: runner does not proceed until approve |
| Simulation | Timeout expires approval |
| Failure | Double submit approve |

---

## T-042–T-046 — Context & observability

| Type | Required |
|------|----------|
| Unit | Masking function strips PII |
| Integration | Context never appears plain in logs in test |
| Replay | T-050 |

---

## T-047–T-052 — Test & CI

| Type | Required |
|------|----------|
| Unit | As above |
| CI | Pipeline fails if test fails; no secrets in logs |

---

## T-053–T-059 — Production

| Type | Required |
|------|----------|
| Unit | Quota math |
| Load | T-056 k6 |
| Simulation | E2E acceptance script |

---

## Cross-cutting logging tests (PRD §12)

- Every handler test should assert **at least one** log line with `task_id` on success and failure paths where applicable.
- AI I/O: tests use redacted fixtures to ensure secrets do not appear in captured log strings.
