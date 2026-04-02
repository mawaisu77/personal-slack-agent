---
name: parallel-independent-work
description: Dispatches separate focused efforts when two or more problems are independent (e.g. unrelated test files or subsystems). Use when failures or tasks do not share state or ordering constraints. Inspired by obra/superpowers dispatching-parallel-agents.
---

# Parallel independent work

## Core idea

One focused context per **independent** problem. Construct **self-contained** prompts: scope, goal, constraints, expected output format. Avoid sharing half-loaded session history across unrelated fixes.

## When to use

- Multiple failures with **different** root causes (e.g. three test files, three bugs).
- Subsystems that can change without stepping on each other.

## When not to use

- Failures are likely related (fix one first).
- Same files or shared mutable state would conflict.
- You have not yet grouped **what** is independent—triage first.

## Pattern

1. **Group** work by domain (e.g. Slack handlers vs Playwright runner).
2. **Prompt** each slice with: specific files, errors, constraints (“do not change X”), deliverable (“summary + diff intent”).
3. **Integrate**: merge results, then run **full** verification (**verification-before-completion**).

## Prompt quality

- **Focused** scope (not “fix everything”).
- **Concrete** errors and file paths.
- **Explicit** “return: root cause + files changed.”

**Attribution:** Inspired by [obra/superpowers — dispatching-parallel-agents](https://github.com/obra/superpowers/tree/main/skills/dispatching-parallel-agents).
