from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

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
from banking_agent.database.repositories import WorkflowRepository
from banking_agent.security.sensitive_data import mask_sensitive_text


class DatabaseWorkflowService:
    """PostgreSQL-backed workflow service for controlled support automation."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = WorkflowRepository(session)

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
            user_request=mask_sensitive_text(user_request),
            customer_id=self._mask_optional_text(customer_id),
            issue_type=issue_type,
            transaction_id=self._mask_optional_text(transaction_id),
            status=initial_status,
            requires_confirmation=requires_confirmation,
            recommended_action=recommended_action,
            created_at=now,
            updated_at=now,
        )

        try:
            saved_workflow = self._repository.add_workflow(workflow)

            self._repository.add_event(
                self._build_event(
                    workflow_id=workflow_id,
                    event_type="workflow_created",
                    message="Support workflow created.",
                    metadata={
                        "issue_type": issue_type,
                        "status": initial_status,
                    },
                )
            )

            if requires_confirmation:
                self._repository.add_event(
                    self._build_event(
                        workflow_id=workflow_id,
                        event_type="confirmation_required",
                        message=(
                            "Workflow requires confirmation before "
                            "action execution."
                        ),
                        metadata={
                            "recommended_action": recommended_action or "",
                        },
                    )
                )

            self._session.commit()

            return saved_workflow

        except Exception:
            self._session.rollback()
            raise

    def get_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Return a workflow by ID."""
        workflow = self._repository.get_workflow(workflow_id)

        if workflow is None:
            raise WorkflowNotFoundError(
                f"Workflow '{workflow_id}' was not found."
            )

        return workflow

    def list_workflows(self) -> list[SupportWorkflow]:
        """Return all workflows, newest created first."""
        return self._repository.list_workflows()

    def list_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Return audit events for a workflow."""
        self.get_workflow(workflow_id)

        return self._repository.list_events(workflow_id)

    def record_intent_classified(
        self,
        workflow_id: str,
        issue_type: IssueType,
    ) -> WorkflowEvent:
        """Record that the request intent was classified."""
        self.get_workflow(workflow_id)

        event = self._build_event(
            workflow_id=workflow_id,
            event_type="intent_classified",
            message="Workflow intent classified.",
            metadata={
                "issue_type": issue_type,
            },
        )

        try:
            saved_event = self._repository.add_event(event)
            self._session.commit()

            return saved_event

        except Exception:
            self._session.rollback()
            raise

    def record_tool_called(
        self,
        workflow_id: str,
        tool_name: str,
        output_summary: str,
    ) -> WorkflowEvent:
        """Record a tool call audit event."""
        self.get_workflow(workflow_id)

        event = self._build_event(
            workflow_id=workflow_id,
            event_type="tool_called",
            message="Workflow tool called.",
            metadata={
                "tool_name": tool_name,
                "output_summary": mask_sensitive_text(output_summary),
            },
        )

        try:
            saved_event = self._repository.add_event(event)
            self._session.commit()

            return saved_event

        except Exception:
            self._session.rollback()
            raise

    def confirm_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Confirm a workflow that is waiting for user approval."""
        workflow = self.get_workflow(workflow_id)

        self._ensure_status(
            workflow=workflow,
            allowed_statuses={"awaiting_confirmation"},
            action="confirm",
        )

        updated_workflow = workflow.model_copy(
            update={
                "status": "approved",
                "updated_at": self._now(),
            }
        )

        try:
            saved_workflow = self._repository.update_workflow(updated_workflow)

            self._repository.add_event(
                self._build_event(
                    workflow_id=workflow_id,
                    event_type="user_confirmed",
                    message="User confirmed the recommended workflow action.",
                )
            )

            self._session.commit()

            return saved_workflow

        except Exception:
            self._session.rollback()
            raise

    def reject_workflow(self, workflow_id: str) -> SupportWorkflow:
        """Reject a workflow that is waiting for user approval."""
        workflow = self.get_workflow(workflow_id)

        self._ensure_status(
            workflow=workflow,
            allowed_statuses={"awaiting_confirmation"},
            action="reject",
        )

        updated_workflow = workflow.model_copy(
            update={
                "status": "rejected",
                "updated_at": self._now(),
            }
        )

        try:
            saved_workflow = self._repository.update_workflow(updated_workflow)

            self._repository.add_event(
                self._build_event(
                    workflow_id=workflow_id,
                    event_type="action_rejected",
                    message="User rejected the recommended workflow action.",
                )
            )

            self._session.commit()

            return saved_workflow

        except Exception:
            self._session.rollback()
            raise

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

        try:
            saved_workflow = self._repository.update_workflow(updated_workflow)

            self._repository.add_event(
                self._build_event(
                    workflow_id=workflow_id,
                    event_type="action_completed",
                    message="Workflow completed.",
                    metadata={
                        "dispute_ticket_id": dispute_ticket_id or "",
                    },
                )
            )

            self._session.commit()

            return saved_workflow

        except Exception:
            self._session.rollback()
            raise

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

        masked_failure_reason = mask_sensitive_text(failure_reason)

        updated_workflow = workflow.model_copy(
            update={
                "status": "failed",
                "updated_at": self._now(),
                "failure_reason": masked_failure_reason,
            }
        )

        try:
            saved_workflow = self._repository.update_workflow(updated_workflow)

            self._repository.add_event(
                self._build_event(
                    workflow_id=workflow_id,
                    event_type="workflow_failed",
                    message="Workflow failed.",
                    metadata={
                        "failure_reason": masked_failure_reason,
                    },
                )
            )

            self._session.commit()

            return saved_workflow

        except Exception:
            self._session.rollback()
            raise

    def _build_event(
        self,
        workflow_id: str,
        event_type: WorkflowEventType,
        message: str,
        metadata: dict[str, str] | None = None,
    ) -> WorkflowEvent:
        """Build an audit event model."""
        return WorkflowEvent(
            event_id=self._new_event_id(),
            workflow_id=workflow_id,
            event_type=event_type,
            message=mask_sensitive_text(message),
            created_at=self._now(),
            metadata=self._mask_metadata(metadata or {}),
        )

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

    def _mask_optional_text(self, value: str | None) -> str | None:
        """Mask sensitive identifiers from optional text values."""
        if value is None:
            return None

        return mask_sensitive_text(value)

    def _mask_metadata(self, metadata: dict[str, str]) -> dict[str, str]:
        """Mask sensitive identifiers from event metadata values."""
        return {
            key: mask_sensitive_text(value)
            for key, value in metadata.items()
        }

    def _new_workflow_id(self) -> str:
        """Create a workflow ID."""
        return f"WF-{uuid4().hex[:8].upper()}"

    def _new_event_id(self) -> str:
        """Create an event ID."""
        return f"EVT-{uuid4().hex[:8].upper()}"

    def _now(self) -> datetime:
        """Return timezone-aware UTC timestamp."""
        return datetime.now(timezone.utc)