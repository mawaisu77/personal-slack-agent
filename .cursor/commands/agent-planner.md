# Planner only (architecture)

**Goal / problem:**

<!-- What to design -->

---

Act as **PLANNER** using subagent **personal-ai-planner** (or label response **Role: PLANNER**).

- Output: Problem Breakdown, Architecture Design, Modules & Interfaces, Data Flow, Failure Scenarios, Success Criteria per component, Human-in-the-Loop Checkpoints, Step-by-Step Implementation Plan.
- **No implementation code.** Ask clarifying questions if requirements are ambiguous.
- Include: Orchestrator, Web (Playwright) agent, Voice agent, Slack (`/do`, `/call`, `/status`, `/cancel`, `/history`), Context Store, DB-backed task state, Approval system, Logging/Observability.
- Default stack: FastAPI, Redis, PostgreSQL, Playwright, Claude API, Vapi/Twilio, S3/R2, AWS Secrets Manager.
