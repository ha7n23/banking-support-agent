from typing import Literal

from pydantic import BaseModel, Field


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