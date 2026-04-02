---
name: writing-implementation-plans
description: Produces bite-sized, file-specific implementation plans from a spec before coding. Use when breaking a feature into tracked tasks, after Planner architecture exists, or when the user wants a checkbox plan with exact paths and test commands. Inspired by obra/superpowers writing-plans.
---

# Writing implementation plans

## When to use

- You have requirements or a **Planner** design and need an **Executor-ready** checklist.
- Prefer **one plan per subsystem** if work is independent.

**Announce:** State that you are using this skill to write the plan.

## Save location

Default: `docs/plans/YYYY-MM-DD-<slug>.md` (override if the user prefers elsewhere).

## Plan header (required)

```markdown
# [Feature] — Implementation Plan

> **Execution:** Use **personal-ai-executor** with **executing-written-plans** (or run tasks inline). Track steps with `- [ ]`.

**Goal:** [one sentence]

**Architecture:** [2–3 sentences, aligned with Planner]

**Tech stack:** [key libs]

---
```

## File map first

Before tasks: list files to **create** / **modify** and each file’s single responsibility. Split by responsibility; follow existing repo patterns.

## Task granularity

Each step is one concrete action (minutes, not days): e.g. failing test → run fail → minimal impl → pass → commit.

## Task template

Per task, include **Files** (exact paths), **checkbox steps**, **commands** (`pytest`, `ruff`, etc.) with **expected outcome**, and **code blocks** for non-trivial code changes—not vague “add error handling.”

## Forbidden placeholders

Do not ship plans with: TBD, “add tests later,” “similar to task N” without repeating content, or steps with no how (no code/command).

## Self-review

1. Every spec requirement maps to a task.
2. No placeholder patterns above.
3. Names/signatures consistent across tasks.

## Handoff

After saving, offer: **(A)** subagent-style task-by-task execution with **personal-ai-verifier** after chunks, or **(B)** inline execution with **executing-written-plans**. Do not start implementation until the user picks or approaches are clear.

**Attribution:** Workflow inspired by [obra/superpowers — writing-plans](https://github.com/obra/superpowers/tree/main/skills/writing-plans).
