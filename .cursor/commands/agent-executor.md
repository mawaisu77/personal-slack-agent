# Executor only (implement)

**Approved design / spec to implement:**

<!-- Paste Planner output or bullet spec -->

---

Act as **EXECUTOR** using subagent **personal-ai-executor** (or label **Role: EXECUTOR**).

- Follow the plan strictly; **do not** redesign architecture unless I explicitly say so.
- Deliver: Folder Structure, File-by-file summary, Code, Setup Instructions, Assumptions.
- Include: retries with backoff, timeouts, stuck detection where designed, screenshots on web failure, persisted task states (`pending` → `running` → `waiting_for_approval` → `completed`/`failed`), HITL before irreversible actions, masked logs, no secrets in code.
- Apply skill **personal-ai-python-standards** and **personal-ai-implementation-workflow** as needed.

If the design is missing or ambiguous, list questions and stop instead of guessing.
