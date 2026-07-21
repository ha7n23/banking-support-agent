from fastapi import APIRouter, Depends, HTTPException, status

from banking_agent.api.dependencies import (
    AgentFactory,
    get_agent_factory,
    get_workflow_service,
)

from banking_agent.api.schemas import (
    DisputeTicketAPIResponse,
    HealthResponse,
    SupportRequest,
    SupportResponse,
    ToolCallAPIResponse,
    WorkflowAPIResponse,
    WorkflowCompleteRequest,
    WorkflowCreateRequest,
    WorkflowEventAPIResponse,
    WorkflowFailRequest,
    WorkflowExecutionResponse,
)

from banking_agent.core.config import APP_NAME, ENVIRONMENT

from banking_agent.core.exceptions import (
    BankingAgentError,
    GenerationError,
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
)

from banking_agent.core.schemas import (
    AgentResponse,
    SupportWorkflow,
    WorkflowEvent,
)

from banking_agent.services.workflow_service import InMemoryWorkflowService
from typing import NoReturn
from banking_agent.routing.router import route_user_request


router = APIRouter()


def to_support_response(
    response: AgentResponse,
    workflow_id: str | None = None,
    workflow_status: str | None = None,
) -> SupportResponse:
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
        workflow_id=workflow_id,
        workflow_status=workflow_status,
    )

def create_workflow_from_agent_response(
    user_request: str,
    response: AgentResponse,
    workflow_service: InMemoryWorkflowService,
) -> tuple[str | None, str | None]:
    """
    Create a support workflow when the agent response needs workflow tracking.

    A workflow is created when:
    - the agent requires confirmation before an action, or
    - the agent created a dispute ticket after confirmation.
    """
    if not response.requires_confirmation and response.dispute_ticket is None:
        return None, None

    route = route_user_request(user_request)

    recommended_action = route.requested_action

    if response.dispute_ticket is not None:
        recommended_action = "create_dispute_ticket"

    workflow = workflow_service.create_workflow(
        user_request=user_request,
        issue_type=(
            response.dispute_ticket.issue_type
            if response.dispute_ticket is not None
            else route.issue_type
        ),
        transaction_id=(
            response.dispute_ticket.transaction_id
            if response.dispute_ticket is not None
            else route.transaction_id
        ),
        requires_confirmation=response.requires_confirmation,
        recommended_action=recommended_action,
    )

    workflow_service.record_intent_classified(
        workflow_id=workflow.workflow_id,
        issue_type=workflow.issue_type,
    )

    for tool_call in response.tool_calls:
        workflow_service.record_tool_called(
            workflow_id=workflow.workflow_id,
            tool_name=tool_call.tool_name,
            output_summary=tool_call.output_summary,
        )

    if response.dispute_ticket is not None:
        workflow = workflow_service.complete_workflow(
            workflow_id=workflow.workflow_id,
            dispute_ticket_id=response.dispute_ticket.ticket_id,
        )

    return workflow.workflow_id, workflow.status

def execute_workflow_action(
    workflow_id: str,
    agent_factory: AgentFactory,
    workflow_service: InMemoryWorkflowService,
) -> WorkflowExecutionResponse:
    """
    Execute an approved workflow action through the controlled agent.

    For this demo, the executable workflow action is creating a mock dispute
    ticket after confirmation.
    """
    workflow = workflow_service.get_workflow(workflow_id)

    if workflow.recommended_action != "create_dispute_ticket":
        raise InvalidWorkflowTransitionError(
            f"Workflow '{workflow_id}' does not have an executable "
            "create_dispute_ticket action."
        )

    if workflow.status == "awaiting_confirmation":
        workflow = workflow_service.confirm_workflow(workflow_id)
    elif workflow.status != "approved":
        raise InvalidWorkflowTransitionError(
            f"Cannot execute workflow '{workflow_id}' from status "
            f"'{workflow.status}'."
        )

    agent = agent_factory(False)

    response = agent.handle_request(
        user_request=workflow.user_request,
        use_llm=False,
        confirm_action=True,
    )

    for tool_call in response.tool_calls:
        workflow_service.record_tool_called(
            workflow_id=workflow_id,
            tool_name=tool_call.tool_name,
            output_summary=tool_call.output_summary,
        )

    if response.dispute_ticket is None:
        failed_workflow = workflow_service.fail_workflow(
            workflow_id=workflow_id,
            failure_reason="Confirmed action did not create a dispute ticket.",
        )

        return WorkflowExecutionResponse(
            workflow=to_workflow_response(failed_workflow),
            support_response=to_support_response(
                response=response,
                workflow_id=workflow_id,
                workflow_status=failed_workflow.status,
            ),
        )

    completed_workflow = workflow_service.complete_workflow(
        workflow_id=workflow_id,
        dispute_ticket_id=response.dispute_ticket.ticket_id,
    )

    return WorkflowExecutionResponse(
        workflow=to_workflow_response(completed_workflow),
        support_response=to_support_response(
            response=response,
            workflow_id=workflow_id,
            workflow_status=completed_workflow.status,
        ),
    )

def to_workflow_response(workflow: SupportWorkflow) -> WorkflowAPIResponse:
    """Convert internal SupportWorkflow into API response schema."""
    return WorkflowAPIResponse(
        workflow_id=workflow.workflow_id,
        user_request=workflow.user_request,
        customer_id=workflow.customer_id,
        issue_type=workflow.issue_type,
        transaction_id=workflow.transaction_id,
        status=workflow.status,
        requires_confirmation=workflow.requires_confirmation,
        recommended_action=workflow.recommended_action,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        failure_reason=workflow.failure_reason,
        dispute_ticket_id=workflow.dispute_ticket_id,
    )


def to_workflow_event_response(
    event: WorkflowEvent,
) -> WorkflowEventAPIResponse:
    """Convert internal WorkflowEvent into API response schema."""
    return WorkflowEventAPIResponse(
        event_id=event.event_id,
        workflow_id=event.workflow_id,
        event_type=event.event_type,
        message=event.message,
        created_at=event.created_at,
        metadata=event.metadata,
    )


def handle_workflow_error(error: BankingAgentError) -> NoReturn:
    """Convert workflow service errors into HTTP errors."""
    if isinstance(error, WorkflowNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if isinstance(error, InvalidWorkflowTransitionError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error),
    ) from error


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
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
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

    workflow_id, workflow_status = create_workflow_from_agent_response(
        user_request=request.user_request,
        response=response,
        workflow_service=workflow_service,
    )

    return to_support_response(
        response=response,
        workflow_id=workflow_id,
        workflow_status=workflow_status,
    )


@router.post(
    "/workflows",
    response_model=WorkflowAPIResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowAPIResponse:
    """Create a controlled support workflow."""
    workflow = workflow_service.create_workflow(
        user_request=request.user_request,
        issue_type=request.issue_type,
        customer_id=request.customer_id,
        transaction_id=request.transaction_id,
        requires_confirmation=request.requires_confirmation,
        recommended_action=request.recommended_action,
    )

    return to_workflow_response(workflow)

@router.get(
    "/workflows",
    response_model=list[WorkflowAPIResponse],
)
def list_workflows(
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> list[WorkflowAPIResponse]:
    """Return all support workflows."""
    workflows = workflow_service.list_workflows()

    return [to_workflow_response(workflow) for workflow in workflows]


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowAPIResponse,
)
def get_workflow(
    workflow_id: str,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowAPIResponse:
    """Return a workflow by ID."""
    try:
        workflow = workflow_service.get_workflow(workflow_id)
    except BankingAgentError as error:
        handle_workflow_error(error)

    return to_workflow_response(workflow)


@router.get(
    "/workflows/{workflow_id}/events",
    response_model=list[WorkflowEventAPIResponse],
)
def list_workflow_events(
    workflow_id: str,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> list[WorkflowEventAPIResponse]:
    """Return audit events for a workflow."""
    try:
        events = workflow_service.list_events(workflow_id)
    except BankingAgentError as error:
        handle_workflow_error(error)

    return [to_workflow_event_response(event) for event in events]


@router.post(
    "/workflows/{workflow_id}/confirm",
    response_model=WorkflowAPIResponse,
)
def confirm_workflow(
    workflow_id: str,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowAPIResponse:
    """Confirm a workflow action that is awaiting approval."""
    try:
        workflow = workflow_service.confirm_workflow(workflow_id)
    except BankingAgentError as error:
        handle_workflow_error(error)

    return to_workflow_response(workflow)


@router.post(
    "/workflows/{workflow_id}/reject",
    response_model=WorkflowAPIResponse,
)
def reject_workflow(
    workflow_id: str,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowAPIResponse:
    """Reject a workflow action that is awaiting approval."""
    try:
        workflow = workflow_service.reject_workflow(workflow_id)
    except BankingAgentError as error:
        handle_workflow_error(error)

    return to_workflow_response(workflow)


@router.post(
    "/workflows/{workflow_id}/complete",
    response_model=WorkflowAPIResponse,
)
def complete_workflow(
    workflow_id: str,
    request: WorkflowCompleteRequest,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowAPIResponse:
    """Complete a workflow."""
    try:
        workflow = workflow_service.complete_workflow(
            workflow_id=workflow_id,
            dispute_ticket_id=request.dispute_ticket_id,
        )
    except BankingAgentError as error:
        handle_workflow_error(error)

    return to_workflow_response(workflow)


@router.post(
    "/workflows/{workflow_id}/fail",
    response_model=WorkflowAPIResponse,
)
def fail_workflow(
    workflow_id: str,
    request: WorkflowFailRequest,
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowAPIResponse:
    """Mark a workflow as failed."""
    try:
        workflow = workflow_service.fail_workflow(
            workflow_id=workflow_id,
            failure_reason=request.failure_reason,
        )
    except BankingAgentError as error:
        handle_workflow_error(error)

    return to_workflow_response(workflow)

@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=WorkflowExecutionResponse,
)
def execute_workflow(
    workflow_id: str,
    agent_factory: AgentFactory = Depends(get_agent_factory),
    workflow_service: InMemoryWorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """Execute an approved workflow action."""
    try:
        return execute_workflow_action(
            workflow_id=workflow_id,
            agent_factory=agent_factory,
            workflow_service=workflow_service,
        )
    except GenerationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except BankingAgentError as error:
        handle_workflow_error(error)