from pydantic import BaseModel, Field


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