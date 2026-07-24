from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from banking_agent.core.schemas import (
    IssueType,
    SupportWorkflow,
    WorkflowEvent,
    WorkflowEventType,
    WorkflowStatus,
)
from banking_agent.database.models import WorkflowEventRecord, WorkflowRecord


class WorkflowRepository:
    """Database access layer for workflow persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_workflow(self, workflow: SupportWorkflow) -> SupportWorkflow:
        """Add a workflow row to the current database transaction."""
        record = self._workflow_to_record(workflow)
        self._session.add(record)
        self._session.flush()

        return self._record_to_workflow(record)

    def get_workflow(self, workflow_id: str) -> SupportWorkflow | None:
        """Return a workflow by ID, or None when it does not exist."""
        record = self._session.get(WorkflowRecord, workflow_id)

        if record is None:
            return None

        return self._record_to_workflow(record)

    def list_workflows(self) -> list[SupportWorkflow]:
        """Return all workflows, newest created first."""
        statement = select(WorkflowRecord).order_by(
            WorkflowRecord.created_at.desc()
        )

        records = self._session.scalars(statement).all()

        return [self._record_to_workflow(record) for record in records]

    def update_workflow(self, workflow: SupportWorkflow) -> SupportWorkflow:
        """Update an existing workflow row in the current transaction."""
        record = self._session.get(WorkflowRecord, workflow.workflow_id)

        if record is None:
            raise ValueError(
                f"Workflow '{workflow.workflow_id}' cannot be updated "
                "because it does not exist."
            )

        record.user_request = workflow.user_request
        record.customer_id = workflow.customer_id
        record.issue_type = workflow.issue_type
        record.transaction_id = workflow.transaction_id
        record.status = workflow.status
        record.requires_confirmation = workflow.requires_confirmation
        record.recommended_action = workflow.recommended_action
        record.failure_reason = workflow.failure_reason
        record.dispute_ticket_id = workflow.dispute_ticket_id
        record.created_at = workflow.created_at
        record.updated_at = workflow.updated_at

        self._session.flush()

        return self._record_to_workflow(record)

    def add_event(self, event: WorkflowEvent) -> WorkflowEvent:
        """Add an audit event row to the current database transaction."""
        record = self._event_to_record(event)
        self._session.add(record)
        self._session.flush()

        return self._record_to_event(record)

    def list_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Return audit events for a workflow in chronological order."""
        statement = (
            select(WorkflowEventRecord)
            .where(WorkflowEventRecord.workflow_id == workflow_id)
            .order_by(WorkflowEventRecord.created_at.asc())
        )

        records = self._session.scalars(statement).all()

        return [self._record_to_event(record) for record in records]

    def _workflow_to_record(
        self,
        workflow: SupportWorkflow,
    ) -> WorkflowRecord:
        """Convert a Pydantic workflow model into a SQLAlchemy record."""
        return WorkflowRecord(
            workflow_id=workflow.workflow_id,
            user_request=workflow.user_request,
            customer_id=workflow.customer_id,
            issue_type=workflow.issue_type,
            transaction_id=workflow.transaction_id,
            status=workflow.status,
            requires_confirmation=workflow.requires_confirmation,
            recommended_action=workflow.recommended_action,
            failure_reason=workflow.failure_reason,
            dispute_ticket_id=workflow.dispute_ticket_id,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
        )

    def _record_to_workflow(
        self,
        record: WorkflowRecord,
    ) -> SupportWorkflow:
        """Convert a SQLAlchemy workflow record into a Pydantic model."""
        return SupportWorkflow(
            workflow_id=record.workflow_id,
            user_request=record.user_request,
            customer_id=record.customer_id,
            issue_type=cast(IssueType, record.issue_type),
            transaction_id=record.transaction_id,
            status=cast(WorkflowStatus, record.status),
            requires_confirmation=record.requires_confirmation,
            recommended_action=record.recommended_action,
            created_at=record.created_at,
            updated_at=record.updated_at,
            failure_reason=record.failure_reason,
            dispute_ticket_id=record.dispute_ticket_id,
        )

    def _event_to_record(
        self,
        event: WorkflowEvent,
    ) -> WorkflowEventRecord:
        """Convert a Pydantic workflow event into a SQLAlchemy record."""
        return WorkflowEventRecord(
            event_id=event.event_id,
            workflow_id=event.workflow_id,
            event_type=event.event_type,
            message=event.message,
            event_metadata=event.metadata,
            created_at=event.created_at,
        )

    def _record_to_event(
        self,
        record: WorkflowEventRecord,
    ) -> WorkflowEvent:
        """Convert a SQLAlchemy event record into a Pydantic model."""
        return WorkflowEvent(
            event_id=record.event_id,
            workflow_id=record.workflow_id,
            event_type=cast(WorkflowEventType, record.event_type),
            message=record.message,
            created_at=record.created_at,
            metadata=record.event_metadata,
        )