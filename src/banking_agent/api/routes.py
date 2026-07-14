from fastapi import APIRouter, Depends, HTTPException, status

from banking_agent.api.dependencies import AgentFactory, get_agent_factory
from banking_agent.api.schemas import (
    DisputeTicketAPIResponse,
    HealthResponse,
    SupportRequest,
    SupportResponse,
    ToolCallAPIResponse,
)
from banking_agent.core.config import APP_NAME, ENVIRONMENT
from banking_agent.core.exceptions import BankingAgentError, GenerationError
from banking_agent.core.schemas import AgentResponse


router = APIRouter()


def to_support_response(response: AgentResponse) -> SupportResponse:
    """Convert internal AgentResponse into API response schema."""
    dispute_ticket = None

    if response.dispute_ticket is not None:
        dispute_ticket = DisputeTicketAPIResponse(
            ticket_id=response.dispute_ticket.ticket_id,
            transaction_id=response.dispute_ticket.transaction_id,
            issue_type=response.dispute_ticket.issue_type,
            status=response.dispute_ticket.status,
            summary=response.dispute_ticket.summary,
            requires_human_review=response.dispute_ticket.requires_human_review,
        )

    return SupportResponse(
        user_request=response.user_request,
        answer=response.answer,
        tool_calls=[
            ToolCallAPIResponse(
                tool_name=tool_call.tool_name,
                input_summary=tool_call.input_summary,
                output_summary=tool_call.output_summary,
            )
            for tool_call in response.tool_calls
        ],
        requires_confirmation=response.requires_confirmation,
        dispute_ticket=dispute_ticket,
    )


@router.get("/")
def root() -> dict[str, str]:
    """Return a simple API root message."""
    return {
        "message": "Banking Support Agent API",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API health status."""
    return HealthResponse(
        status="ok",
        app_name=APP_NAME,
        environment=ENVIRONMENT,
    )


@router.post("/support", response_model=SupportResponse)
def handle_support_request(
    request: SupportRequest,
    agent_factory: AgentFactory = Depends(get_agent_factory),
) -> SupportResponse:
    """Handle a banking support request through the controlled agent."""
    try:
        agent = agent_factory(request.use_llm)
        response = agent.handle_request(
            user_request=request.user_request,
            use_llm=request.use_llm,
            confirm_action=request.confirm_action,
        )
    except GenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except BankingAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return to_support_response(response)  