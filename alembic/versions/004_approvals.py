"""approvals table (T-037)

Revision ID: 004_approvals
Revises: 003_cancel_req
Create Date: 2026-04-02

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "004_approvals"
down_revision = "003_cancel_req"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    approval_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="approval_status",
        create_type=False,
    )
    approval_status.create(bind, checkfirst=True)

    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_summary", sa.Text(), nullable=False),
        sa.Column("screenshot_url", sa.Text(), nullable=True),
        sa.Column("status", approval_status, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approvals_task_id", "approvals", ["task_id"], unique=False)
    op.create_index("ix_approvals_status", "approvals", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_approvals_status", table_name="approvals")
    op.drop_index("ix_approvals_task_id", table_name="approvals")
    op.drop_table("approvals")
    op.execute(sa.text("DROP TYPE IF EXISTS approval_status"))
