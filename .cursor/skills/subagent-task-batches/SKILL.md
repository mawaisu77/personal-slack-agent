---
name: subagent-task-batches
description: Runs implementation plans task-by-task with fresh subagent context per task and review between tasks. Use when a plan has independent checkbox tasks and the platform supports Task/subagents—reduces context pollution. Inspired by obra/superpowers subagent-driven-development.
---

# Subagent task batches

## Idea

For each **plan task**: dispatch a narrow **Executor**-style run with only that task’s text + file list + constraints. After the task: **spec alignment** (matches plan?) then **quality** (readable, secure?). Map to this repo: **personal-ai-executor** → **personal-ai-verifier** on the task slice → continue or fix.

## When

- Plan has **independent** tasks (from **writing-implementation-plans**).
- Subagents or isolated runs are available.

## When not

- Tightly coupled tasks—use sequential **executing-written-plans** in one session.
- No plan—brainstorm/design first (**personal-ai-planner**).

## Rules

- Do not parallelize two implementers on the **same** files.
- Provide full task text to the worker; do not rely on “read the plan” without copying the section.
- If status is **BLOCKED**, change inputs, split the task, or escalate—do not retry identical prompts blindly.

## Model choice (if applicable)

- Mechanical, small-scope tasks → faster/cheaper models.
- Integration across many files or ambiguous behavior → more capable models.
- Review/architecture → strongest model.

**Attribution:** Inspired by [obra/superpowers — subagent-driven-development](https://github.com/obra/superpowers/tree/main/skills/subagent-driven-development).
