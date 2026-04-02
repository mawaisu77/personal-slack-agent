---
name: review-handoff
description: Prepares a focused review for personal-ai-reviewer after substantive changes—scope summary, requirements pointer, and optional git range. Use before merge or when completing a major task. Inspired by obra/superpowers requesting-code-review.
---

# Review handoff

**Core idea:** Give **personal-ai-reviewer** (or a human) everything needed to judge the **artifact**, not the chat history.

## When

- After a feature slice, before merge to main, or when **personal-ai-verifier** is satisfied and you want a principal pass.

## What to include

1. **What changed** — bullet list of behavior and modules touched.
2. **Requirements** — pointer to Planner doc, `docs/plans/…`, or ticket acceptance criteria.
3. **How to verify** — exact commands already run (attach evidence per **verification-before-completion**).
4. **Git range (optional)** — `BASE_SHA`/`HEAD_SHA` or branch name for diff review.

## After feedback

- **Critical** — fix before merge.
- **Important** — fix before merge unless explicitly deferred.
- **Minor** — backlog unless trivial.

Escalate to **personal-ai-planner** if feedback implies architectural change.

**Attribution:** Inspired by [obra/superpowers — requesting-code-review](https://github.com/obra/superpowers/tree/main/skills/requesting-code-review).
