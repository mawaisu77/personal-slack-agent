"""add cancel_requested_at on tasks (T-009)

Revision ID: 003_cancel_req
Revises: 002_checkpoints
Create Date: 2026-04-02

"""

import sqlalchemy as sa

from alembic import op

revision = "003_cancel_req"
down_revision = "002_checkpoints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tasks", "cancel_requested_at")
