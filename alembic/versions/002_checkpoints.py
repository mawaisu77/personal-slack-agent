"""checkpoints table for resume (T-002).

Revision ID: 002_checkpoints
Revises: 001_tasks
Create Date: 2026-04-02

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "002_checkpoints"
down_revision = "001_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "sequence", name="uq_checkpoints_task_sequence"),
    )
    op.create_index("ix_checkpoints_task_id", "checkpoints", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_checkpoints_task_id", table_name="checkpoints")
    op.drop_table("checkpoints")
