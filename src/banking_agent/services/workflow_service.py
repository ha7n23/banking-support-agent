from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from banking_agent.core.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
)
from banking_agent.core.schemas import (
    IssueType,
    SupportWorkflow,
    WorkflowEvent,
    WorkflowEventType,
    WorkflowStatus,
)

class WorkflowServiceProtocol(Protocol):
    """Contract shared by workflow storage implementations."""

    def create_workflow(
        self,
        user_request: str,
        issue_type: IssueType,
        transaction_id: str | None = None,
        customer_id: str | None = None,
        requires_confirmation: bool = False,
        recommended_action: str | None = None,
    ) -> SupportWorkflow:
        """Create a new support workflow and initial audit events."""
        ...

    def get_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Return a workflow by ID."""
        ...

    def list_workflows(self) -> list[SupportWorkflow]:
        """Return all workflows, newest created first."""
        ...

    def list_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Return audit events for a workflow."""
        ...

    def record_intent_classified(
        self,
        workflow_id: str,
        issue_type: IssueType,
    ) -> WorkflowEvent:
        """Record that the request intent was classified."""
        ...

    def record_tool_called(
        self,
        workflow_id: str,
        tool_name: str,
        output_summary: str,
    ) -> WorkflowEvent:
        """Record a tool call audit event."""
        ...

    def confirm_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Confirm a workflow that is waiting for user approval."""
        ...

    def reject_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Reject a workflow that is waiting for user approval."""
        ...

    def complete_workflow(
        self,
        workflow_id: str,
        dispute_ticket_id: str | None = None,
    ) -> SupportWorkflow:
        """Mark a workflow as completed."""
        ...

    def fail_workflow(
        self,
        workflow_id: str,
        failure_reason: str,
    ) -> SupportWorkflow:
        """Mark a workflow as failed."""
        ...

class InMemoryWorkflowService:
    """
    In-memory workflow service for controlled support automation.

    This is intentionally simple for the portfolio project. In production,
    workflows and audit events would be stored in a database.
    """

    def __init__(self) -> None:
        self._workflows: dict[str, SupportWorkflow] = {}
        self._events: dict[str, list[WorkflowEvent]] = {}

    def create_workflow(
        self,
        user_request: str,
        issue_type: IssueType,
        transaction_id: str | None = None,
        customer_id: str | None = None,
        requires_confirmation: bool = False,
        recommended_action: str | None = None,
    ) -> SupportWorkflow:
        """Create a new support workflow and initial audit events."""
        now = self._now()
        workflow_id = self._new_workflow_id()

        initial_status: WorkflowStatus = (
            "awaiting_confirmation" if requires_confirmation else "created"
        )

        workflow = SupportWorkflow(
            workflow_id=workflow_id,
            user_request=user_request,
            customer_id=customer_id,
            issue_type=issue_type,
            transaction_id=transaction_id,
            status=initial_status,
            requires_confirmation=requires_confirmation,
            recommended_action=recommended_action,
            created_at=now,
            updated_at=now,
        )

        self._workflows[workflow_id] = workflow
        self._events[workflow_id] = []

        self._record_event(
            workflow_id=workflow_id,
            event_type="workflow_created",
            message="Support workflow created.",
            metadata={
                "issue_type": issue_type,
                "status": initial_status,
            },
        )

        if requires_confirmation:
            self._record_event(
                workflow_id=workflow_id,
                event_type="confirmation_required",
                message="Workflow requires confirmation before action execution.",
                metadata={
                    "recommended_action": recommended_action or "",
                },
            )

        return workflow

    def get_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Return a workflow by ID."""
        workflow = self._workflows.get(workflow_id)

        if workflow is None:
            raise WorkflowNotFoundError(
                f"Workflow '{workflow_id}' was not found."
            )

        return workflow

    def list_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Return audit events for a workflow."""
        self.get_workflow(workflow_id)

        return list(self._events[workflow_id])

    def record_intent_classified(
        self,
        workflow_id: str,
        issue_type: IssueType,
    ) -> WorkflowEvent:
        """Record that the request intent was classified."""
        return self._record_event(
            workflow_id=workflow_id,
            event_type="intent_classified",
            message="Workflow intent classified.",
            metadata={
                "issue_type": issue_type,
            },
        )

    def record_tool_called(
        self,
        workflow_id: str,
        tool_name: str,
        output_summary: str,
    ) -> WorkflowEvent:
        """Record a tool call audit event."""
        return self._record_event(
            workflow_id=workflow_id,
            event_type="tool_called",
            message="Workflow tool called.",
            metadata={
                "tool_name": tool_name,
                "output_summary": output_summary,
            },
        )

    def confirm_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Confirm a workflow that is waiting for user approval."""
        workflow = self.get_workflow(workflow_id)

        self._ensure_status(
            workflow=workflow,
            allowed_statuses={"awaiting_confirmation"},
            action="confirm",
        )

        updated_workflow = self._update_workflow_status(
            workflow=workflow,
            status="approved",
        )

        self._record_event(
            workflow_id=workflow_id,
            event_type="user_confirmed",
            message="User confirmed the recommended workflow action.",
        )

        return updated_workflow

    def reject_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Reject a workflow that is waiting for user approval."""
        workflow = self.get_workflow(workflow_id)

        self._ensure_status(
            workflow=workflow,
            allowed_statuses={"awaiting_confirmation"},
            action="reject",
        )

        updated_workflow = self._update_workflow_status(
            workflow=workflow,
            status="rejected",
        )

        self._record_event(
            workflow_id=workflow_id,
            event_type="action_rejected",
            message="User rejected the recommended workflow action.",
        )

        return updated_workflow

    def complete_workflow(
        self,
        workflow_id: str,
        dispute_ticket_id: str | None = None,
    ) -> SupportWorkflow:
        """Mark a workflow as completed."""
        workflow = self.get_workflow(workflow_id)

        self._ensure_status(
            workflow=workflow,
            allowed_statuses={"created", "approved"},
            action="complete",
        )

        updated_workflow = workflow.model_copy(
            update={
                "status": "completed",
                "updated_at": self._now(),
                "dispute_ticket_id": dispute_ticket_id,
            }
        )

        self._workflows[workflow_id] = updated_workflow

        self._record_event(
            workflow_id=workflow_id,
            event_type="action_completed",
            message="Workflow completed.",
            metadata={
                "dispute_ticket_id": dispute_ticket_id or "",
            },
        )

        return updated_workflow

    def fail_workflow(
        self,
        workflow_id: str,
        failure_reason: str,
    ) -> SupportWorkflow:
        """Mark a workflow as failed."""
        workflow = self.get_workflow(workflow_id)

        if workflow.status in {"completed", "rejected"}:
            raise InvalidWorkflowTransitionError(
                f"Cannot fail workflow '{workflow_id}' from status "
                f"'{workflow.status}'."
            )

        updated_workflow = workflow.model_copy(
            update={
                "status": "failed",
                "updated_at": self._now(),
                "failure_reason": failure_reason,
            }
        )

        self._workflows[workflow_id] = updated_workflow

        self._record_event(
            workflow_id=workflow_id,
            event_type="workflow_failed",
            message="Workflow failed.",
            metadata={
                "failure_reason": failure_reason,
            },
        )

        return updated_workflow

    def _record_event(
        self,
        workflow_id: str,
        event_type: WorkflowEventType,
        message: str,
        metadata: dict[str, str] | None = None,
    ) -> WorkflowEvent:
        """Record an audit event for a workflow."""
        self.get_workflow(workflow_id)

        event = WorkflowEvent(
            event_id=self._new_event_id(),
            workflow_id=workflow_id,
            event_type=event_type,
            message=message,
            created_at=self._now(),
            metadata=metadata or {},
        )

        self._events[workflow_id].append(event)

        return event

    def _update_workflow_status(
        self,
        workflow: SupportWorkflow,
        status: WorkflowStatus,
    ) -> SupportWorkflow:
        """Update workflow status and timestamp."""
        updated_workflow = workflow.model_copy(
            update={
                "status": status,
                "updated_at": self._now(),
            }
        )

        self._workflows[workflow.workflow_id] = updated_workflow

        return updated_workflow

    def _ensure_status(
        self,
        workflow: SupportWorkflow,
        allowed_statuses: set[WorkflowStatus],
        action: str,
    ) -> None:
        """Validate workflow status before a transition."""
        if workflow.status not in allowed_statuses:
            raise InvalidWorkflowTransitionError(
                f"Cannot {action} workflow '{workflow.workflow_id}' "
                f"from status '{workflow.status}'."
            )
        
    def list_workflows(self) -> list[SupportWorkflow]:
        """Return all workflows, newest created first."""
        return list(reversed(self._workflows.values()))

    def _new_workflow_id(self) -> str:
        """Create a workflow ID."""
        return f"WF-{uuid4().hex[:8].upper()}"

    def _new_event_id(self) -> str:
        """Create an event ID."""
        return f"EVT-{uuid4().hex[:8].upper()}"

    def _now(self) -> datetime:
        """Return timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc)