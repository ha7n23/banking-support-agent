from typing import Literal

from pydantic import BaseModel, Field

from datetime import datetime


TransactionChannel = Literal["qr", "card", "mobile_app", "unknown"]

TransactionStatusValue = Literal[
    "deducted",
    "successful",
    "failed",
    "pending",
    "duplicate_charge",
    "not_found",
]

SettlementStatus = Literal[
    "settled",
    "not_settled",
    "pending",
    "unknown",
]

IssueType = Literal[
    "qr_payment_dispute",
    "duplicate_card_charge",
    "password_reset",
    "refund_timeline",
    "general",
]

TicketStatus = Literal[
    "created",
    "not_created",
]

WorkflowStatus = Literal[
    "created",
    "awaiting_confirmation",
    "approved",
    "completed",
    "rejected",
    "failed",
]


WorkflowEventType = Literal[
    "workflow_created",
    "intent_classified",
    "tool_called",
    "confirmation_required",
    "user_confirmed",
    "action_completed",
    "action_rejected",
    "workflow_failed",
]


class TransactionStatus(BaseModel):
    """Result returned by the transaction status tool."""

    transaction_id: str
    status: TransactionStatusValue
    channel: TransactionChannel
    amount: float | None = None
    merchant_received: bool | None = None
    settlement_status: SettlementStatus = "unknown"


class PolicyContext(BaseModel):
    """Policy context returned by the policy retrieval tool."""

    issue_type: IssueType
    summary: str
    source: str
    section: str


class DisputeEligibility(BaseModel):
    """Decision-support result for dispute eligibility."""

    transaction_id: str
    issue_type: IssueType
    eligible: bool
    reason: str
    requires_human_review: bool = False

class DisputeTicket(BaseModel):
    """Mock dispute ticket created after explicit confirmation."""

    ticket_id: str
    transaction_id: str
    issue_type: IssueType
    status: TicketStatus
    summary: str
    requires_human_review: bool = True


class ToolCallRecord(BaseModel):
    """Record of a tool call made during an agent run."""

    tool_name: str
    input_summary: str
    output_summary: str


class AgentResponse(BaseModel):
    """Final response returned by the support agent."""

    user_request: str
    answer: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    requires_confirmation: bool = False
    dispute_ticket: DisputeTicket | None = None

class AgentRoute(BaseModel):
    """Routing decision for a user support request."""

    issue_type: IssueType
    transaction_id: str | None = None
    needs_transaction_lookup: bool = False
    needs_policy_context: bool = True
    needs_dispute_eligibility: bool = False
    requested_action: str | None = None
    requires_confirmation: bool = False

class SupportWorkflow(BaseModel):
    """State record for a support automation workflow."""

    workflow_id: str
    user_request: str
    customer_id: str | None = None
    issue_type: IssueType
    transaction_id: str | None = None
    status: WorkflowStatus
    requires_confirmation: bool = False
    recommended_action: str | None = None
    created_at: datetime
    updated_at: datetime
    failure_reason: str | None = None
    dispute_ticket_id: str | None = None


class WorkflowEvent(BaseModel):
    """Audit event created during a support workflow."""

    event_id: str
    workflow_id: str
    event_type: WorkflowEventType
    message: str
    created_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)