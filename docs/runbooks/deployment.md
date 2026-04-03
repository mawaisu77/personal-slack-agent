# Deployment (T-058)

## Components

- **Slack gateway**: FastAPI + Bolt (`uvicorn personal_ai.slack_interface.app:create_app --factory`).
- **Worker**: `python -m personal_ai.run.runner` (or your process supervisor).
- **PostgreSQL**: migrations via `alembic upgrade head`.
- **Redis**: job queue + DLQ keys.

## Environment

Set at minimum:

- `DATABASE_URL`, `REDIS_URL`
- `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`
- Optional: `APPROVAL_POLICY_PATH`, `MAX_CONCURRENT_TASKS_PER_USER`, `MAX_DAILY_TASKS_PER_USER`
- `AGENT_WEB_MODE=loop` for real browser automation in workers

## Cron / jobs

- **Approval expiry (T-041)**: schedule `python -m personal_ai.approvals.expiry_cli` every 1–5 minutes.

## Health

- HTTP `GET /health` on the Slack gateway service.

## Docker

```bash
docker compose up --build
```

Wire real secrets via `.env` or your secret manager; do not commit tokens.

## Database

```bash
alembic upgrade head
```

Run from the same image/version as the application code you deploy.
