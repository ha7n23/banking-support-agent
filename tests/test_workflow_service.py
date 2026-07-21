import pytest

from banking_agent.core.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
)
from banking_agent.services.workflow_service import InMemoryWorkflowService


def test_create_workflow_records_initial_state_and_event() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="My QR payment TX1001 failed.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
    )

    assert workflow.workflow_id.startswith("WF-")
    assert workflow.status == "created"
    assert workflow.issue_type == "qr_payment_dispute"
    assert workflow.transaction_id == "TX1001"
    assert workflow.requires_confirmation is False

    events = service.list_events(workflow.workflow_id)

    assert len(events) == 1
    assert events[0].event_type == "workflow_created"
    assert events[0].workflow_id == workflow.workflow_id


def test_create_workflow_requiring_confirmation_starts_awaiting_confirmation() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )

    assert workflow.status == "awaiting_confirmation"
    assert workflow.requires_confirmation is True
    assert workflow.recommended_action == "create_dispute_ticket"

    events = service.list_events(workflow.workflow_id)
    event_types = [event.event_type for event in events]

    assert event_types == [
        "workflow_created",
        "confirmation_required",
    ]


def test_confirm_workflow_moves_to_approved_and_records_event() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )

    confirmed_workflow = service.confirm_workflow(workflow.workflow_id)

    assert confirmed_workflow.status == "approved"

    events = service.list_events(workflow.workflow_id)
    event_types = [event.event_type for event in events]

    assert "user_confirmed" in event_types


def test_reject_workflow_moves_to_rejected_and_records_event() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )

    rejected_workflow = service.reject_workflow(workflow.workflow_id)

    assert rejected_workflow.status == "rejected"

    events = service.list_events(workflow.workflow_id)
    event_types = [event.event_type for event in events]

    assert "action_rejected" in event_types


def test_complete_workflow_moves_to_completed_and_records_ticket_id() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="My QR payment TX1001 failed.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
    )

    completed_workflow = service.complete_workflow(
        workflow_id=workflow.workflow_id,
        dispute_ticket_id="DSP-TX1001",
    )

    assert completed_workflow.status == "completed"
    assert completed_workflow.dispute_ticket_id == "DSP-TX1001"

    events = service.list_events(workflow.workflow_id)
    event_types = [event.event_type for event in events]

    assert "action_completed" in event_types


def test_fail_workflow_moves_to_failed_and_records_reason() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="My QR payment TX1001 failed.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
    )

    failed_workflow = service.fail_workflow(
        workflow_id=workflow.workflow_id,
        failure_reason="Mock tool failure.",
    )

    assert failed_workflow.status == "failed"
    assert failed_workflow.failure_reason == "Mock tool failure."

    events = service.list_events(workflow.workflow_id)
    event_types = [event.event_type for event in events]

    assert "workflow_failed" in event_types


def test_confirm_rejected_workflow_is_invalid() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )

    service.reject_workflow(workflow.workflow_id)

    with pytest.raises(InvalidWorkflowTransitionError):
        service.confirm_workflow(workflow.workflow_id)


def test_complete_awaiting_confirmation_workflow_is_invalid() -> None:
    service = InMemoryWorkflowService()

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )

    with pytest.raises(InvalidWorkflowTransitionError):
        service.complete_workflow(workflow.workflow_id)


def test_unknown_workflow_raises_error() -> None:
    service = InMemoryWorkflowService()

    with pytest.raises(WorkflowNotFoundError):
        service.get_workflow("WF-UNKNOWN")

def test_list_workflows_returns_all_workflows_newest_first() -> None:
    service = InMemoryWorkflowService()

    first_workflow = service.create_workflow(
        user_request="First request.",
        issue_type="general",
    )

    second_workflow = service.create_workflow(
        user_request="Second request.",
        issue_type="password_reset",
    )

    workflows = service.list_workflows()

    assert len(workflows) == 2
    assert workflows[0].workflow_id == second_workflow.workflow_id
    assert workflows[1].workflow_id == first_workflow.workflow_id