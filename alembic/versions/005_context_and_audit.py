"""add user_context and approval_audit tables (T-042, T-046)

Revision ID: 005_context_audit
Revises: 004_approvals
Create Date: 2026-04-03
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "005_context_audit"
down_revision = "004_approvals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_context",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("context_key", sa.String(length=128), nullable=False),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("encryption_version", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_user_context_user_id", "user_context", ["user_id"], unique=False)
    op.create_index(
        "ix_user_context_user_key",
        "user_context",
        ["user_id", "context_key"],
        unique=True,
    )

    op.create_table(
        "approval_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["approval_id"], ["approvals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approval_audit_approval_id",
        "approval_audit",
        ["approval_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_audit_created_at",
        "approval_audit",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_approval_audit_created_at", table_name="approval_audit")
    op.drop_index("ix_approval_audit_approval_id", table_name="approval_audit")
    op.drop_table("approval_audit")
    op.drop_index("ix_user_context_user_key", table_name="user_context")
    op.drop_index("ix_user_context_user_id", table_name="user_context")
    op.drop_table("user_context")
