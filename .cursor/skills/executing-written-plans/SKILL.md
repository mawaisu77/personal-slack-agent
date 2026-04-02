---
name: executing-written-plans
description: Executes a saved markdown implementation plan with checkpoints, todos, and stops on blockers. Use when a plan file exists in docs/plans/ or when batching Executor work from checkbox tasks. Inspired by obra/superpowers executing-plans.
---

# Executing written plans

**Announce:** State that you are using this skill.

## Process

### 1. Load and critique

1. Read the plan file end-to-end.
2. Note gaps, unclear steps, or risky ordering—raise with the user **before** coding.
3. Create a todo list mirroring tasks; mark one task `in_progress`.

### 2. Execute tasks

For each task:

1. Follow steps **in order**; run every verification command the plan specifies.
2. Do not skip “run test and expect FAIL/PASS” steps.
3. On blocker (missing dep, failing verify, ambiguous instruction): **stop** and ask—do not guess.

### 3. Completion gate

When all tasks are done:

- Run **verification-before-completion** (fresh commands, evidence before claims).
- Invoke **personal-ai-verifier** on the scope; fix issues per **personal-ai-executor**.
- Optional: **personal-ai-reviewer** for merge/release.

## Stop conditions

- Blocker, repeated verification failure, or plan error → stop; escalate or revise plan.
- Do **not** implement on `main`/`master` without explicit user consent (use a branch/worktree if the user wants isolation).

## Integration

- **writing-implementation-plans** — produces the plan this skill runs.
- **personal-ai-implementation-workflow** — repo-specific scaffolding order.
- **parallel-independent-work** — if tasks are independent and the platform supports parallel agents.

**Attribution:** Inspired by [obra/superpowers — executing-plans](https://github.com/obra/superpowers/tree/main/skills/executing-plans).
