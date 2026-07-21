from pydantic import BaseModel, Field

from datetime import datetime

from banking_agent.core.schemas import (
    IssueType,
    WorkflowEventType,
    WorkflowStatus,
)


class HealthResponse(BaseModel):
    """Basic API health response."""

    status: str
    app_name: str
    environment: str


class SupportRequest(BaseModel):
    """Request body for the banking support agent."""

    user_request: str = Field(..., min_length=1)
    use_llm: bool = False
    confirm_action: bool = False


class ToolCallAPIResponse(BaseModel):
    """Tool call record returned through the API."""

    tool_name: str
    input_summary: str
    output_summary: str


class DisputeTicketAPIResponse(BaseModel):
    """Mock dispute ticket returned through the API."""

    ticket_id: str
    transaction_id: str
    issue_type: str
    status: str
    summary: str
    requires_human_review: bool


class SupportResponse(BaseModel):
    """Response body returned by the support agent endpoint."""

    user_request: str
    answer: str
    tool_calls: list[ToolCallAPIResponse]
    requires_confirmation: bool
    dispute_ticket: DisputeTicketAPIResponse | None = None
    workflow_id: str | None = None
    workflow_status: str | None = None

class WorkflowCreateRequest(BaseModel):
    """Request body for creating a support workflow."""

    user_request: str = Field(..., min_length=1)
    issue_type: IssueType
    customer_id: str | None = None
    transaction_id: str | None = None
    requires_confirmation: bool = False
    recommended_action: str | None = None


class WorkflowCompleteRequest(BaseModel):
    """Request body for completing a workflow."""

    dispute_ticket_id: str | None = None


class WorkflowFailRequest(BaseModel):
    """Request body for failing a workflow."""

    failure_reason: str = Field(..., min_length=1)


class WorkflowAPIResponse(BaseModel):
    """Workflow state returned through the API."""

    workflow_id: str
    user_request: str
    customer_id: str | None
    issue_type: IssueType
    transaction_id: str | None
    status: WorkflowStatus
    requires_confirmation: bool
    recommended_action: str | None
    created_at: datetime
    updated_at: datetime
    failure_reason: str | None
    dispute_ticket_id: str | None


class WorkflowEventAPIResponse(BaseModel):
    """Workflow audit event returned through the API."""

    event_id: str
    workflow_id: str
    event_type: WorkflowEventType
    message: str
    created_at: datetime
    metadata: dict[str, str]

class WorkflowExecutionResponse(BaseModel):
    """Response returned after executing an approved workflow action."""

    workflow: WorkflowAPIResponse
    support_response: SupportResponse