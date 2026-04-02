# Four-role pipeline (full)

Run the **Planner → Executor → Verifier → Reviewer** pipeline for this repo. Use project subagents: `personal-ai-planner`, `personal-ai-executor`, `personal-ai-verifier`, `personal-ai-reviewer`.

**User request / feature:**

<!-- Describe what to build or change below, or paste Planner output -->

---

**Instructions for the agent:**

1. **PLANNER** — Use the **personal-ai-planner** subagent (or adopt Role: PLANNER). Produce design only: Problem Breakdown, Architecture, Modules & Interfaces, Data Flow, Failure Scenarios, Success Criteria, HITL checkpoints, Step-by-Step Plan. No implementation code.
2. Wait for my **approval** of the design (or say "approved — proceed").
3. **EXECUTOR** — Use **personal-ai-executor** (Role: EXECUTOR). Implement per plan; folder structure, code, setup, assumptions.
4. **VERIFIER** — Use **personal-ai-verifier** (Role: VERIFIER). Test scenarios (happy/edge/failure), bugs, missing cases, risk, suggested fixes.
5. If Verifier finds issues — **EXECUTOR** fixes, then **VERIFIER** re-runs until satisfied.
6. **REVIEWER** — Use **personal-ai-reviewer** (Role: REVIEWER). Holistic audit; Final Decision: Approve / Reject / Changes required.

Apply skills when relevant: `personal-ai-python-standards`, `personal-ai-implementation-workflow`, `personal-ai-quality-gates`. One role per step unless I ask otherwise.
