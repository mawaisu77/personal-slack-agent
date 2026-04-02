---
name: verification-before-completion
description: Requires running verification commands and capturing evidence before any success or completion claim—use before commits, PRs, or telling the user work is done. Applies to Executor and Verifier roles. Inspired by obra/superpowers verification-before-completion.
---

# Verification before completion

**Core rule:** **Evidence before claims.** If you have not run the verification command in this turn, you cannot say tests pass, build is green, or the bug is fixed.

## Gate (follow in order)

1. **Identify** the command that proves the claim (tests, lint, build, manual repro).
2. **Run** the full command fresh in this session.
3. **Read** full output and exit code.
4. **Only then** state success—and quote or summarize evidence (e.g. “0 failures”, “exit 0”).

Skipping a step is not verification.

## Common mistakes

| Wrong | Right |
|-------|--------|
| “Should pass now” | Run `pytest` / `ruff` / `docker build` and show result |
| Earlier run was green | Re-run before claiming |
| Linter clean = build OK | Run the actual build/test that matters |
| Agent said “done” | Check diff + run verification yourself |

## Red flags—do not claim success if you are about to say

“Probably,” “seems fine,” “looks correct,” “Done!” without a fresh command output.

## When this applies

Before: merge, PR, “task complete,” moving to the next task, or any positive statement about correctness.

Pairs with **personal-ai-verifier** (scenarios) and **systematic-debugging** (root cause before fixes).

**Attribution:** Inspired by [obra/superpowers — verification-before-completion](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion).
