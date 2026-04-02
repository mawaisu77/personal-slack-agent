# Implementation Phases — Personal AI Assistant Agent

**Source:** `docs/product-prd.md` v3.0 (April 2026)  
**Purpose:** Milestones with goals, deliverables, and success criteria.

---

## Phase 1: Foundation

**Goal:** Establish persistent task lifecycle, queue-backed orchestration, configuration/secrets, and minimal service skeletons so downstream features attach to stable contracts.

**Deliverables**

- PostgreSQL schemas for tasks, jobs, checkpoints, approvals (tables/migrations).
- Redis (or SQS-compatible abstraction) queue with job schema, FIFO+priority hooks, retry + exponential backoff, Dead Letter Queue.
- Orchestrator service: enqueue, parse job types (`web` | `call`), dispatch to workers, state transitions (`pending` → `running` → `waiting_for_approval` | terminal states).
- Task State Manager: CRUD + transitions; support `cancelled` from any state; resume/retry metadata.
- Agent Runner service skeleton: holds execution state, interfaces stubbed for AI and tools.
- Project structure for modular services (per PRD §2.1).
- Secrets Manager integration; no plaintext secrets in repo.
- Baseline structured logging (correlation IDs).

**Success criteria**

- Tasks persist across process restarts; illegal transitions rejected.
- Jobs retry with backoff and land in DLQ when exhausted.
- Cancellation updates DB and stops in-flight work per design (worker cooperative cancel).
- `ack` path for Slack events measurable (target &lt;2s in Phase 4 when wired).

---

## Phase 2: Web Automation Core

**Goal:** Implement Playwright-based Browser Automation Service and full AI agent loop with validation, limits, and screenshot capture per PRD §5–7, §11.

**Deliverables**

- Playwright (headless Chromium): persistent profile + isolated browser context per task.
- Agent loop: capture (screenshot + DOM) → AI → structured action → execute → validate → repeat.
- Mandatory action schema (`click | type | scroll | wait | extract`); validation layer (success, no-op detection).
- Limits: max 3 cycles without progress; max duration 5 minutes per PRD §5.1.
- Interaction retries (min 3 attempts per PRD §7); navigation validation.
- Screenshot storage (e.g. S3/R2) URLs for observability and approvals.
- Error path: screenshot + log + user notification hooks.

**Success criteria**

- End-to-end dry-run: synthetic page or fixture completes loop with logged steps.
- Stuck/no-progress and global timeout enforced deterministically.
- AI I/O logged per observability rules (redacted where needed).

---

## Phase 3: Voice Agent

**Goal:** Deliver Voice Service for outbound calls with real-time conversation, phone-tree handling, and transcript + summary return per PRD §9.

**Deliverables**

- Provider integration (Vapi / Bland / Retell per PRD); abstraction for swap/testing.
- Call flow: resolve target number (minimal implementation per PRD), place call, stream/handle conversation.
- Return artifact: transcript + summary to orchestrator/task record.
- Error handling and task failure propagation to state `failed`.

**Success criteria**

- At least one provider works in staging with test number or sandbox.
- Task records store transcript/summary references; failures logged.

---

## Phase 4: Slack + Approval System

**Goal:** Slack Gateway Service for `/do`, `/call`, `/status`, `/cancel`, `/history`; sub-2s acknowledgments; Approval Service with blocking behavior and Slack interactive approve/reject per PRD §8, §16.

**Deliverables**

- Slack app: command and interaction handlers; async pattern for long work.
- Orchestrator integration: user commands create/query/cancel tasks.
- Approval Service: approval object persistence; block agent execution; `expires_at` and timeout handling.
- Triggers: payments, irreversible actions, uncertainty (policy hooks).
- User-visible: action summary + screenshot URL on approval request.

**Success criteria**

- Commands registered and documented; status/history reflect DB truth.
- Tasks cannot complete sensitive actions without `approved` when policy requires it.
- Approval timeouts move task to failed or safe state per spec.

---

## Phase 5: Observability + Security

**Goal:** Observability Service (logs, traces, replay) and security hardening per PRD §12–13.

**Deliverables**

- Log all actions, AI inputs/outputs (redacted), screenshot references; support replay/debug trace.
- Context Store Service: structured schema, minimal retrieval, masked sensitive fields in logs/API.
- Encryption at rest for sensitive columns/secrets paths; least-privilege IAM patterns documented.
- Audit trail for approvals and state changes.

**Success criteria**

- Given a `task_id`, an operator can reconstruct major steps from logs + stored artifacts.
- Security review checklist passes (no secrets in code, encryption documented).

---

## Phase 6: Testing + CI/CD

**Goal:** Mandatory test pyramid and automated pipelines per PRD §14.

**Deliverables**

- Unit tests: agent logic, state machine, validation, parsers.
- Integration tests: browser + AI (mocked LLM), queue, DB.
- Replay tests: recorded traces re-executed or validated.
- CI: lint, test, artifact build; CD pipeline definition (env-specific).

**Success criteria**

- CI green on main; tests block merge on failure.
- Coverage targets documented (critical paths for state + agent loop).

---

## Phase 7: Production Readiness

**Goal:** Performance, cost controls, failure recovery, and acceptance criteria per PRD §15–18.

**Deliverables**

- Checkpoints per step; resume from last valid state (PRD §15).
- Performance: concurrent tasks, queue workers scaled; `ack` &lt;2s validated under load.
- Cost controls: AI call limits per task; budget caps per user (PRD §17).
- Runbooks: deploy, rollback, DLQ replay, on-call checks.
- Final acceptance demo: E2E web + approval + logging + recovery.

**Success criteria**

- PRD §18 acceptance: E2E execution, approval enforced, full logging, recovery demonstrated.
- Documented SLOs and limits; safety/determinism/observability prioritized over raw speed (PRD §20).

---

## Phase dependency note

Implementation **order** within phases follows prioritization: core infrastructure and state first, then web loop, then Slack/approval wiring, then voice, then observability/security depth, then testing/CI, then production hardening. Task-level dependencies are in `dependencies.json`.
