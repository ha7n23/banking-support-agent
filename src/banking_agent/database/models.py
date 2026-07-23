from __future__ import annotations

from datetime import datetime
from typing import get_args

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from banking_agent.core.schemas import (
    IssueType,
    WorkflowEventType,
    WorkflowStatus,
)


def _in_constraint_sql(column_name: str, allowed_values: tuple[str, ...]) -> str:
    """Build SQL for a CHECK constraint from app Literal values."""
    quoted_values = ", ".join(f"'{value}'" for value in allowed_values)
    return f"{column_name} IN ({quoted_values})"


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class WorkflowRecord(Base):
    """Database row for the current state of a support workflow."""

    __tablename__ = "workflows"

    __table_args__ = (
        CheckConstraint(
            _in_constraint_sql("issue_type", get_args(IssueType)),
            name="workflows_issue_type_check",
        ),
        CheckConstraint(
            _in_constraint_sql("status", get_args(WorkflowStatus)),
            name="workflows_status_check",
        ),
        Index("idx_workflows_status", "status"),
        Index("idx_workflows_issue_type", "issue_type"),
        Index("idx_workflows_created_at", "created_at"),
    )

    workflow_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    customer_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_type: Mapped[str] = mapped_column(Text, nullable=False)
    transaction_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispute_ticket_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    events: Mapped[list[WorkflowEventRecord]] = relationship(
        back_populates="workflow",
    )


class WorkflowEventRecord(Base):
    """Database row for an append-only workflow audit event."""

    __tablename__ = "workflow_events"

    __table_args__ = (
        CheckConstraint(
            _in_constraint_sql("event_type", get_args(WorkflowEventType)),
            name="workflow_events_event_type_check",
        ),
        Index(
            "idx_workflow_events_workflow_id_created_at",
            "workflow_id",
            "created_at",
        ),
    )

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("workflows.workflow_id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # SQLAlchemy's declarative base already uses the name "metadata",
    # so the Python attribute is event_metadata while the DB column is metadata.
    event_metadata: Mapped[dict[str, str]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    workflow: Mapped[WorkflowRecord] = relationship(
        back_populates="events",
    )