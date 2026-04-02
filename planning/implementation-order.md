# Implementation Order — Personal AI Assistant Agent

**Source:** `planning/dependencies.json` · **Tasks:** `planning/tasks.md`  
**Method:** Topological sort of the full dependency DAG, grouped into parallel batches. Within each batch every task can be worked concurrently; a batch cannot start until all tasks in all prior batches are complete.

> **Key insight:** The original phase ordering (P1 → P2 → P3 → P4 → P5 → P6 → P7) is logically correct but treats phases as hard sequential gates. The true dependency graph allows Voice (P3), Approval DB (P4), Observability setup (P5), and Testing infra (P6) to start significantly earlier — shortening the critical path by ~2–3 sprints.

---

## Critical path

The longest chain of sequential dependencies:

```
T-001 → T-003 → T-004 → T-007 → T-012
                                  ↓
T-015 → T-017 → T-018 → T-020 → T-022 → T-023 → T-026 → T-048 → T-051 → T-052
```

Everything else runs in parallel alongside this spine.

---

## Batch schedule

### Batch 1 — Zero-dependency foundations
*All three can start on day one. Unlock the entire system.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-001 | DB schema: tasks & lifecycle | STATE | M |
| T-010 | Secrets Manager wiring | SEC | S |
| T-015 | Correlation & structured logging | OBS | S |

**Unlocks:** T-002, T-003, T-008, T-011, T-014, T-016 (and via T-010: T-017, T-028, T-037)

---

### Batch 2 — Schema, API contracts, app skeletons
*All deps in Batch 1. Start immediately after Batch 1.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-002 | DB schema: checkpoints & resume | STATE | M |
| T-003 | Job schema & enqueue API | QUEUE | S |
| T-008 | Lifecycle API (internal) | STATE | M |
| T-011 | Encryption at rest plan | SEC | M |
| T-014 | AI client contract | RUN | M |
| T-016 | Slack app bootstrap (foundation) | SLACK | M |

**Unlocks:** T-004, T-007, T-009, T-017, T-028, T-037, T-042, T-044, T-047

---

### Batch 3 — Queue consumer, first service integrations, early tests
*⚡ Early-start for Voice (T-028), Approval DB (T-037), AI logging (T-044), unit tests (T-047) — all normally labeled Phase 3–6 but only need Batch 1–2 deps.*

| ID | Title | Module | C | Original phase |
|----|-------|--------|---|----------------|
| T-004 | Redis queue consumer + FIFO/priority | QUEUE | M | P1 |
| T-009 | Cancellation propagation | ORCH | M | P1 |
| T-017 | Playwright session manager | WEB | M | P2 |
| **T-028** | **Voice provider abstraction** | **VOICE** | **M** | **P3 → early** |
| **T-037** | **Approval persistence** | **APPR** | **S** | **P4 → early** |
| **T-044** | **AI I/O logging** | **OBS** | **M** | **P5 → early** |
| **T-047** | **Unit tests: state machine** | **TEST** | **M** | **P6 → early** |

**Unlocks:** T-005, T-007 (needs T-004), T-018, T-029, T-042, T-045, T-046

---

### Batch 4 — Orchestrator, Playwright capture, Voice call, observability depth
*T-007 (Orchestrator dispatch) is the central unlock for web + Slack + voice routing.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-005 | Retry + exponential backoff | QUEUE | M |
| T-007 | Orchestrator enqueue & dispatch | ORCH | M |
| T-018 | Capture: DOM + screenshot | WEB | M |
| T-029 | Outbound call execution | VOICE | L |
| T-042 | Context schema & storage | CTX | M |
| T-045 | Replay / debug trace store | OBS | M |
| T-046 | Audit log for approvals | APPR | S |

**Unlocks:** T-006, T-012, T-019, T-020, T-030, T-031, T-033, T-043, T-050

---

### Batch 5 — DLQ, Runner, full web stack, Voice pipeline complete, /do command
*T-012 (Agent Runner) and T-020 (Action executor) are both available here — two of the three most complex tasks.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-006 | Dead Letter Queue | QUEUE | S |
| T-012 | Agent Runner process skeleton | RUN | M |
| T-019 | Screenshot storage URLs | WEB | S |
| T-020 | Action executor (click/type/scroll/wait/extract) | WEB | L |
| T-030 | Number resolution hook | VOICE | S |
| T-031 | Transcript + summary artifact | VOICE | M |
| T-033 | `/do` command | SLACK | M |
| T-043 | Masked retrieval for agents | CTX | M |
| T-050 | Replay tests | TEST | M |

**Unlocks:** T-013, T-021, T-022, T-032, T-035

---

### Batch 6 — Execution state, interaction validation, Voice routing, Slack queries
*Fills in the remaining integrations before the agent loop assembles.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-013 | Execution state store | RUN | S |
| T-021 | Interaction retry (min 3) | WEB | S |
| T-022 | Navigation validation | WEB | M |
| T-032 | Route call jobs through Voice | ORCH | M |
| T-035 | `/status`, `/cancel`, `/history` | SLACK | M |

**Unlocks:** T-023, T-034, T-036

---

### Batch 7 — Agent loop integration (core AI loop)
*T-023 is the most critical task in the system — it wires capture → AI → execute → validate. Do not start until all Batch 6 deps are clean.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-023 | Agent loop integration | RUN | L |
| T-034 | `/call` command | SLACK | M |
| T-036 | Async updates for long tasks | SLACK | M |

**Unlocks:** T-024, T-025, T-026, T-027, T-038, T-039, T-053, T-055, T-049

---

### Batch 8 — Safety systems, approval gate, error pipeline, perf + checkpoint
*All agent safety constraints land here: no-progress, timeout, no-op, approval blocking.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-024 | No-progress detection (3 cycles) | RUN | M |
| T-025 | Max duration 5 minutes | RUN | S |
| T-026 | Validation layer (no-op detection) | RUN | M |
| T-027 | Error: screenshot + notify | WEB | S |
| T-038 | Block execution on approval | RUN | L |
| T-039 | Slack interactive approve/reject | SLACK | M |
| T-049 | Integration: mock AI + browser | TEST | L |
| T-053 | Cost controls: AI call limits | RUN | S |
| T-055 | Checkpoint integration | RUN | M |

**Unlocks:** T-040, T-041, T-048, T-054, T-056, T-057, T-059

---

### Batch 9 — Approval policy, budget caps, production validation, acceptance
*Finishing touches on approval system, budget enforcement, load testing, and the acceptance demo.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-040 | Approval triggers policy | APPR | M |
| T-041 | Approval timeout | APPR | S |
| T-048 | Unit tests: validation & action parsing | TEST | S |
| T-054 | Budget caps per user | ORCH | M |
| T-056 | Load test: ack <2s | INFRA | M |
| T-057 | Concurrent tasks scale | ORCH | M |
| T-059 | Acceptance demo script | DOC | M |

**Unlocks:** T-051 (needs T-047 from B3 + T-048 + T-049 + T-050 — all now done)

---

### Batch 10 — CI pipeline
*Depends on all test tasks completing (T-047 B3, T-048 B9, T-049 B8, T-050 B5).*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-051 | CI pipeline (lint + test + checks) | CICD | M |

**Unlocks:** T-052, T-058

---

### Batch 11 — Deploy pipeline + runbooks
*Final deliverables. System is production-shippable after this batch.*

| ID | Title | Module | C |
|----|-------|--------|---|
| T-052 | Build & deploy pipeline | CICD | M |
| T-058 | Runbooks & on-call | DOC | S |

---

## Sprint plan (1-week sprints, 2–3 engineers)

| Sprint | Batches | Focus |
|--------|---------|-------|
| **S1** | B1 + B2 | DB schema, secrets, logging, lifecycle API, AI contract, Slack skeleton |
| **S2** | B3 | Queue consumer, Playwright session, Voice abstraction, Approval DB, AI I/O logging, first unit tests |
| **S3** | B4 | Orchestrator dispatch, Playwright capture, outbound call, context schema, replay store |
| **S4** | B5 | DLQ, Agent Runner, action executor, Voice pipeline, `/do` command, masked context |
| **S5** | B6 + B7 | Interaction retries, nav validation, Slack queries, **agent loop integration** |
| **S6** | B8 | Safety guards (no-progress, timeout, no-op), approval blocking, error pipeline, checkpoint |
| **S7** | B9 | Approval policy + timeout, budget caps, load test, unit tests for validation, acceptance demo |
| **S8** | B10 + B11 | CI/CD pipeline, deploy pipeline, runbooks |

---

## Parallel tracks summary

Two largely independent tracks can run after Sprint 1:

```
Track A (Web + Agent loop — critical path)
B3: T-017 (Playwright)
B4: T-018 (Capture)
B5: T-020 (Actions)
B6: T-021, T-022 (Retry, Nav)
B7: T-023 (Agent loop) ← critical path convergence

Track B (Voice + Approval — parallel)
B3: T-028 (Provider abstraction), T-037 (Approval DB)
B4: T-029 (Call execution), T-046 (Audit log)
B5: T-030, T-031 (Number, Transcript)
B6: T-032 (Route call jobs)
B8: T-038, T-039 (Approval gate, Slack buttons)
```

Observability and Context (T-044, T-045, T-042, T-043) run as a **Track C** alongside both, starting from B3.

---

## Early-start moves vs original phase assignment

Tasks that can start earlier than their labeled phase if the team has capacity:

| Task | Original phase | Earliest possible batch | Why it can move |
|------|---------------|------------------------|-----------------|
| T-028 Voice abstraction | P3 | **B3** | Only needs T-010 (B1) |
| T-037 Approval persistence | P4 | **B3** | Only needs T-001 (B1) |
| T-044 AI I/O logging | P5 | **B3** | Only needs T-014, T-015 (B1–2) |
| T-047 Unit tests: state machine | P6 | **B3** | Only needs T-008 (B2) |
| T-042 Context schema | P5 | **B4** | Only needs T-011 (B2) |
| T-045 Replay trace store | P5 | **B4** | Only needs T-044 (B3) |
| T-046 Audit log | P5 | **B4** | Only needs T-037 (B3) |
| T-033 `/do` command | P4 | **B5** | Needs T-007 (B4) — available before full Slack phase |
| T-050 Replay tests | P6 | **B5** | Only needs T-045 (B4) |
| T-053 AI call limits | P7 | **B8** | Only needs T-023 (B7) |
| T-055 Checkpoint integration | P7 | **B8** | Needs T-002 (B2), T-023 (B7) |
| T-059 Acceptance demo script | P7 | **B9** | Deps satisfied after B8 |

---

## Quick-reference: ordered task list

Flat list in topological order (batch number in parentheses):

```
[B1]  T-001  T-010  T-015
[B2]  T-002  T-003  T-008  T-011  T-014  T-016
[B3]  T-004  T-009  T-017  T-028  T-037  T-044  T-047
[B4]  T-005  T-007  T-018  T-029  T-042  T-045  T-046
[B5]  T-006  T-012  T-019  T-020  T-030  T-031  T-033  T-043  T-050
[B6]  T-013  T-021  T-022  T-032  T-035
[B7]  T-023  T-034  T-036
[B8]  T-024  T-025  T-026  T-027  T-038  T-039  T-049  T-053  T-055
[B9]  T-040  T-041  T-048  T-054  T-056  T-057  T-059
[B10] T-051
[B11] T-052  T-058
```

Total: 59 tasks across 11 batches / 8 sprints.

---

## Related documents

| Document | Purpose |
|----------|---------|
| `planning/tasks.md` | Full task catalog with acceptance criteria |
| `planning/subtasks.md` | Step-by-step implementation steps per task |
| `planning/dependencies.json` | Machine-readable dependency graph |
| `planning/phases.md` | Original phase delivery plan |
| `planning/test-plan.md` | Test requirements per task |
