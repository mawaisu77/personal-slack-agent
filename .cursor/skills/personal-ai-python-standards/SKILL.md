---
name: personal-ai-python-standards
description: Applies production Python and FastAPI conventions for the Personal AI Assistant stack. Use when writing or refactoring backend code, APIs, workers, or shared libraries; when the user asks for style, structure, typing, or FastAPI patterns; or when reviewing Python changes for consistency.
---

# Python and FastAPI standards

## Package layout

- **One concept per package** (`orchestrator/`, `agents/web/`, `slack/`, `state/`, `approvals/`). Avoid dumping unrelated code in `utils.py`.
- **Dependency direction**: domain/core ← infrastructure (DB, Redis, Slack client). No circular imports.
- **Settings**: single `config` or `settings` module loaded from env; validate required vars at startup (e.g. Pydantic `BaseSettings`).

## Typing and APIs

- Type **public** functions and Pydantic models for I/O boundaries (HTTP, queues, DB rows mapped to models).
- FastAPI: explicit `response_model`, `status_code`, and dependency-injected services—not globals.
- Prefer `TypedDict` or Pydantic for structured dicts; avoid untyped `dict` across module boundaries.

## Errors and resilience

- Wrap external calls (HTTP, DB, Redis, Playwright, Slack, Vapi) with **timeouts** and **retries with exponential backoff** where idempotent or safe.
- Raise or return **domain-specific errors**; map them to HTTP/Slack-safe messages at the edge. Never leak stack traces or secrets to users.
- Log failures with **correlation/task IDs**; mask tokens and PII in log messages.

## Async

- Use `async` for I/O-bound paths consistently; avoid blocking calls inside async routes (use thread pool or sync endpoints only when justified).

## Security in code

- **No secrets** in source. Read from env or secret manager only.
- Validate and normalize inputs at API boundaries; least-privilege DB roles in deployment docs.

## When unsure

- Match existing project patterns first; if none, prefer small modules and explicit interfaces over clever one-liners.
