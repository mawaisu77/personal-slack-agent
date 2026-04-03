"""One-shot cron/worker entry: ``python -m personal_ai.approvals.expiry_cli``."""

from __future__ import annotations

from personal_ai.approvals.expiry import expire_overdue_approvals
from personal_ai.db.session import session_scope
from personal_ai.observability.logging import configure_logging, get_logger

log = get_logger(__name__)


def main() -> None:
    configure_logging(json_logs=False)
    with session_scope() as session:
        n = expire_overdue_approvals(session)
    log.info("approval_expiry_run", expired=n)


if __name__ == "__main__":
    main()
