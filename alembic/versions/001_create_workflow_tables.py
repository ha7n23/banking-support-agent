"""create workflow tables

Revision ID: 001_create_workflow_tables
Revises:
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "001_create_workflow_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create workflow persistence tables."""
    op.create_table(
        "workflows",
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("user_request", sa.Text(), nullable=False),
        sa.Column("customer_id", sa.Text(), nullable=True),
        sa.Column("issue_type", sa.Text(), nullable=False),
        sa.Column("transaction_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "requires_confirmation",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("dispute_ticket_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "issue_type IN ("
            "'qr_payment_dispute', "
            "'duplicate_card_charge', "
            "'password_reset', "
            "'refund_timeline', "
            "'general'"
            ")",
            name="workflows_issue_type_check",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'created', "
            "'awaiting_confirmation', "
            "'approved', "
            "'completed', "
            "'rejected', "
            "'failed'"
            ")",
            name="workflows_status_check",
        ),
        sa.PrimaryKeyConstraint("workflow_id"),
    )

    op.create_index(
        "idx_workflows_status",
        "workflows",
        ["status"],
    )
    op.create_index(
        "idx_workflows_issue_type",
        "workflows",
        ["issue_type"],
    )
    op.create_index(
        "idx_workflows_created_at",
        "workflows",
        ["created_at"],
    )

    op.create_table(
        "workflow_events",
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("workflow_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event_type IN ("
            "'workflow_created', "
            "'intent_classified', "
            "'tool_called', "
            "'confirmation_required', "
            "'user_confirmed', "
            "'action_completed', "
            "'action_rejected', "
            "'workflow_failed'"
            ")",
            name="workflow_events_event_type_check",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"],
            ["workflows.workflow_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )

    op.create_index(
        "idx_workflow_events_workflow_id_created_at",
        "workflow_events",
        ["workflow_id", "created_at"],
    )


def downgrade() -> None:
    """Drop workflow persistence tables."""
    op.drop_index(
        "idx_workflow_events_workflow_id_created_at",
        table_name="workflow_events",
    )
    op.drop_table("workflow_events")

    op.drop_index("idx_workflows_created_at", table_name="workflows")
    op.drop_index("idx_workflows_issue_type", table_name="workflows")
    op.drop_index("idx_workflows_status", table_name="workflows")
    op.drop_table("workflows")