"""tasks table: lifecycle states, payload, retries (T-001).

Revision ID: 001_tasks
Revises:
Create Date: 2026-04-02

Downgrade: drops `tasks` and ENUM types `task_status`, `task_type` (PostgreSQL).

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "001_tasks"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    task_status = postgresql.ENUM(
        "pending",
        "running",
        "waiting_for_approval",
        "completed",
        "failed",
        "cancelled",
        name="task_status",
        create_type=False,
    )
    task_type = postgresql.ENUM("web", "call", name="task_type", create_type=False)
    task_status.create(bind, checkfirst=True)
    task_type.create(bind, checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("type", task_type, nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("retry_count", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("retry_count >= 0", name="ck_tasks_retry_count_non_negative"),
    )
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"], unique=False)
    op.create_index("ix_tasks_user_status", "tasks", ["user_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_user_status", table_name="tasks")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_table("tasks")
    op.execute(sa.text("DROP TYPE IF EXISTS task_type"))
    op.execute(sa.text("DROP TYPE IF EXISTS task_status"))
