# Epics — Personal AI Assistant Agent

**Source:** `docs/product-prd.md` v3.0

Each epic maps to PRD §2.1 services and cross-cutting concerns. Components are implementable units; dependencies list other epics or external systems.

---

## E-ORCH — Orchestrator System

**Description:** Parses tasks from queue payloads, manages lifecycle transitions, dispatches work to Agent Runner, enforces policies (cost limits, cancellation). Central to PRD §2.1 (Orchestrator Service) and §3–4.

**Components**

- Job ingestion from queue; mapping `type: web | call` to handlers.
- State transition orchestration; coordination with Task State Manager.
- Checkpoint coordination for resume (PRD §15).
- Integration with Approval Service before sensitive steps.

**Dependencies:** E-STATE, E-QUEUE, E-CTX (read), E-APPR (gate), E-OBS (emit logs)

---

## E-QUEUE — Queue & Job Infrastructure

**Description:** Redis (BullMQ) or AWS SQS-style abstraction; FIFO with priority; exponential backoff retries; Dead Letter Queue. PRD §4.

**Components**

- Job schema: `task_id`, `user_id`, `type`, `payload`, `priority`, `retries`.
- Producer/consumer libraries; DLQ consumer tooling.
- Retry policy configuration aligned with Orchestrator.

**Dependencies:** E-STATE (task existence), infrastructure (Redis/SQS)

---

## E-STATE — Task State Manager

**Description:** Authoritative persistence for task lifecycle: `pending`, `running`, `waiting_for_approval`, `completed`, `failed`, `cancelled`; retry/resume/cancel. PRD §3.

**Components**

- DB migrations; optimistic locking or row versioning for transitions.
- APIs for workers to claim/update state; cancellation signals.
- Checkpoint storage for resume.

**Dependencies:** PostgreSQL

---

## E-RUN — Agent Runner Service

**Description:** Executes the AI agent loop, maintains execution state, calls AI with PRD §5–6 contracts. PRD §2.1 Agent Runner Service.

**Components**

- Loop controller: cycle limits, duration cap (5 min), no-progress cap (3 cycles).
- AI adapter: structured JSON in/out; reasoning field handling.
- Integration with Browser and Voice backends.

**Dependencies:** E-ORCH, E-WEB (web tasks), E-VOICE (call tasks), E-OBS, E-CTX, E-APPR

---

## E-WEB — Web Automation Agent (Browser Service)

**Description:** Playwright headless Chromium; persistent profile; isolated sessions; action execution and validation. PRD §7 + §5.2–5.3.

**Components**

- Session manager (profile + per-task context).
- DOM + screenshot capture; action executor (`click | type | scroll | wait | extract`).
- Validation layer; min 3 interaction retries; navigation checks.

**Dependencies:** E-RUN, object storage (screenshots), E-OBS

---

## E-VOICE — Voice Agent

**Description:** Outbound calls via Vapi/Bland/Retell; real-time conversation; phone tree; transcript + summary. PRD §9.

**Components**

- Provider client abstraction; webhook/stream handling if required.
- Number resolution hook (minimal per PRD).
- Post-call artifact attachment to task.

**Dependencies:** E-RUN, E-OBS, secrets for provider keys

---

## E-SLACK — Slack Gateway Service

**Description:** Commands `/do`, `/call`, `/status`, `/cancel`, `/history`; acknowledgments &lt;2s; async updates. PRD §2.1, §16.

**Components**

- Slack Bolt (or equivalent) app; signing secret verification.
- Command handlers → Orchestrator APIs; interactive components for approvals.
- Rate limiting / user scoping as needed.

**Dependencies:** E-ORCH, E-STATE, E-APPR (interactions)

---

## E-APPR — Approval System

**Description:** Approval objects; block execution; Slack approve/reject; expiry/timeout. PRD §8.

**Components**

- Persistence for approval_id, task_id, action_summary, screenshot_url, status, expires_at.
- Worker blocking until resolved or timeout policy.
- Triggers: payments, irreversible actions, uncertainty (configurable policies).

**Dependencies:** E-STATE, E-SLACK (UI), object storage (screenshots)

---

## E-CTX — Context Store Service

**Description:** Structured user data; secure access; load minimal fields; mask in logs. PRD §10.

**Components**

- Schema + encrypted storage for PII columns (with E-SEC).
- Retrieval API for agents with field-level allowlists.

**Dependencies:** E-SEC, PostgreSQL

---

## E-OBS — Logging & Observability Service

**Description:** Log actions, AI I/O, screenshots; replay/debug trace. PRD §12.

**Components**

- Correlation IDs across services; structured JSON logs.
- Trace store for replay tests; redaction pipeline.

**Dependencies:** Log sink, optional OpenTelemetry

---

## E-SEC — Security Layer

**Description:** Secrets Manager; encryption at rest; no plaintext credentials; least privilege. PRD §13.

**Components**

- Central config loading; secret rotation hooks.
- KMS/DB encryption for sensitive columns; IAM documentation.

**Dependencies:** Cloud provider or local dev equivalents

---

## E-TEST — Testing Framework

**Description:** Unit, integration, replay tests per PRD §14.

**Components**

- Fixtures, mocks for AI and browser; test DB/Redis.
- Replay harness reading Observability traces.

**Dependencies:** All feature epics (consumes)

---

## E-CICD — CI/CD Pipeline

**Description:** Automated test runs and deployment pipelines. PRD §14.

**Components**

- Lint + test gates; build images; env-specific deploy.

**Dependencies:** E-TEST

---

## Epic dependency graph (summary)

```
E-SEC (foundational) ─┬→ E-STATE, E-QUEUE, E-CTX, E-OBS
E-STATE ← E-QUEUE → E-ORCH → E-RUN ─┬→ E-WEB
                                    └→ E-VOICE
E-APPR ← E-ORCH, E-SLACK, E-WEB (screenshots)
E-SLACK → E-ORCH
E-CTX → E-RUN, E-WEB
E-OBS → (all services emit)
E-TEST → consumes all
E-CICD → E-TEST
```
