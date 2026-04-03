# Incident response (T-058)

## Severity

- **SEV1**: data breach, total outage, payment impact — page on-call immediately.
- **SEV2**: partial outage, elevated errors — investigate within 30 minutes.
- **SEV3**: degraded performance — next business day unless trending worse.

## First steps

1. Confirm scope (Slack gateway only vs worker vs database vs Redis).
2. Check recent deploys and feature flags (`AGENT_WEB_MODE`, `APPROVAL_POLICY_PATH`).
3. Pull logs with `task_id` / `user_id` correlation from structured logs.
4. For web tasks: locate screenshot URL in Slack or object storage for the failing step.

## Common failures

| Symptom | Likely cause | Action |
|--------|----------------|--------|
| Queue grows, no progress | Workers down / Redis unreachable | Scale workers; verify `REDIS_URL`. |
| Tasks stuck `waiting_for_approval` | Slack interactivity URL misconfigured | Verify Request URL and signing secret. |
| All users blocked | Budget caps (`MAX_*_TASKS_PER_USER`) | Raise caps or identify abuse. |
| Playwright failures | Browser crash / OOM | Restart worker; reduce concurrency. |

## Rollback

- Revert to previous container image or git tag.
- Run DB migrations backward only with a reviewed down migration.

## Post-incident

- File a short timeline, root cause, and follow-up issues (tests, alerts, runbook updates).
