#!/usr/bin/env bash
# T-059 — minimal acceptance checklist (lint + unit tests + optional browser test).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ ! -d .venv ]]; then
  echo "Create a venv first: python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'"
  exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "== ruff =="
ruff check personal_ai tests alembic
echo "== pytest =="
pytest tests/ -q
echo "OK — extend with RUN_BROWSER_INTEGRATION=1 playwright install for browser smoke test."
