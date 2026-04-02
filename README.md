# Personal AI Assistant

Production-oriented backend for a **Slack-driven multi-agent assistant**: task lifecycle, Redis-backed job queue, web automation (Playwright), voice provider hooks, approvals, and structured observability.

See **`docs/product-prd.md`** for product requirements and **`docs/system-architecture.md`** for the service map. Implementation batches are tracked in **`planning/implementation-order.md`**.

## Requirements

- **Python** 3.11+
- **PostgreSQL** (migrations via Alembic)
- **Redis** (job queue)
- **Slack app** credentials for the HTTP gateway (`SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`)

Optional: **Docker** and Docker Compose for local Postgres and Redis.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: set DATABASE_URL, REDIS_URL, Slack secrets, etc.
```

Start dependencies (example):

```bash
docker compose up -d postgres redis
```

Run database migrations:

```bash
alembic upgrade head
```

Install Playwright browsers when you run web automation locally:

```bash
playwright install chromium
```

### Run the Slack HTTP app (FastAPI + Bolt)

```bash
uvicorn personal_ai.slack_interface.app:create_app --factory --host 0.0.0.0 --port 8000
```

Expose `/health` and `/slack/events` to your Slack app’s Request URL (HTTPS in production).

## Configuration

Secrets are loaded via **`get_secret()`** (`personal_ai/config/secrets.py`):

- **`SECRETS_MODE=env`**: read from the process environment (typical for local dev and `.env`).
- **`SECRETS_MODE=aws`**: load a JSON bundle from AWS Secrets Manager (`AWS_REGION`, `AWS_APP_SECRET_ID`).

Never commit real tokens. Use **`.env.example`** as a template only.

Notable settings (see **`personal_ai/config/settings.py`**):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Sync SQLAlchemy URL (psycopg3), e.g. `postgresql+psycopg://...` |
| `REDIS_URL` | Redis for the job queue |
| `PLAYWRIGHT_USER_DATA_DIR` | Directory reserved for browser profile / storage state |
| `VOICE_PROVIDER` | `noop` (default) until a real provider is wired |
| `LOG_FORMAT=json` | Structured JSON logs (correlation fields from context) |

## Development

```bash
pytest
ruff check personal_ai tests alembic
```

## Package layout

| Path | Role |
|------|------|
| `personal_ai/config/` | Settings and secrets |
| `personal_ai/db/` | SQLAlchemy base and sessions |
| `personal_ai/state/` | Tasks, checkpoints, approvals |
| `personal_ai/queue/` | Job payloads and Redis queue |
| `personal_ai/orchestrator/` | Lifecycle and cancellation |
| `personal_ai/run/` | AI contract validation, cancel signals |
| `personal_ai/web/` | Playwright session manager |
| `personal_ai/voice/` | Voice provider abstraction |
| `personal_ai/slack_interface/` | FastAPI + Slack Bolt |
| `personal_ai/observability/` | Logging and AI I/O redaction |
| `alembic/` | Migrations |
| `tests/` | Unit tests |

## License

Add a license file if you distribute this repository publicly.
