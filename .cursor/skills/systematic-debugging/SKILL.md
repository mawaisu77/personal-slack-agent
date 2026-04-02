---
name: systematic-debugging
description: Root-cause-first debugging for failures, flaky tests, and unexpected behavior—before proposing fixes. Use when investigating errors, CI failures, or production issues. Inspired by obra/superpowers systematic-debugging.
---

# Systematic debugging

**Iron rule:** No fix without root-cause investigation. Symptom-only patches count as failure.

## Phase 1 — Investigate

1. Read errors/stack traces completely (file, line, codes).
2. **Reproduce** reliably; record exact steps.
3. Check **recent changes** (`git diff`, deps, config, env).
4. In multi-layer systems (Slack → API → DB → worker), add **short-lived** logging at boundaries to see where data goes wrong—then narrow.

## Phase 2 — Pattern

Find a **working** analogue in the repo; diff against the broken path (behavior, config, assumptions).

## Phase 3 — Hypothesis

One hypothesis at a time; **smallest** change to test it. If wrong, new hypothesis—do not stack unrelated fixes.

## Phase 4 — Fix

1. Prefer a **minimal repro** or failing test first.
2. One fix addressing the **root** cause; avoid drive-by refactors.
3. Verify with **verification-before-completion** (fresh command output).

## If 3+ fixes failed

Stop thrashing: likely **architecture** or wrong layer—discuss with the user / **personal-ai-planner** before another random fix.

## Red flags (stop and return to Phase 1)

“Quick patch,” “try changing X,” multiple changes at once, no repro, “probably fixed.”

**Attribution:** Inspired by [obra/superpowers — systematic-debugging](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging).
