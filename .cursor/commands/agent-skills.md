# Project skills & standards (reference)

## Subagents (`.cursor/agents/`)

`personal-ai-planner` · `personal-ai-executor` · `personal-ai-verifier` · `personal-ai-reviewer`

## Rules (`.cursor/rules/`)

Four-role pipeline, stack defaults, Slack/HITL, security, Playwright, etc.

## Core skills (`.cursor/skills/`)

| Skill | When |
|-------|------|
| **personal-ai-python-standards** | Python/FastAPI style, typing, errors, security in code |
| **personal-ai-implementation-workflow** | Scaffold feature from plan → shipped code |
| **personal-ai-quality-gates** | Pre-merge checklist; Verifier → Reviewer |

## Workflow enhancements (inspired by [obra/superpowers](https://github.com/obra/superpowers/tree/main/skills))

| Skill | When |
|-------|------|
| **writing-implementation-plans** | Checkbox plans with file paths; save under `docs/plans/` |
| **executing-written-plans** | Run a saved plan with checkpoints and blockers |
| **verification-before-completion** | Evidence before “tests pass” / “done” claims |
| **parallel-independent-work** | Multiple unrelated failures or tasks in parallel |
| **systematic-debugging** | Root cause before fixes |
| **review-handoff** | Package context for **personal-ai-reviewer** |
| **subagent-task-batches** | One subagent/task from a plan + per-task verify |

Tell me the task; I will apply the matching skill and role.
