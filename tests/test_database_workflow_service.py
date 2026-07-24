from collections.abc import Generator
import os

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from banking_agent.core.config import DATABASE_URL
from banking_agent.core.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowNotFoundError,
)
from banking_agent.services.database_workflow_service import (
    DatabaseWorkflowService,
)
from banking_agent.database.connection import get_session_factory


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DATABASE_TESTS") != "1" or not DATABASE_URL,
        reason=(
            "Database integration tests require RUN_DATABASE_TESTS=1 "
            "and DATABASE_URL."
        ),
    ),
]


@pytest.fixture()
def database_session() -> Generator[tuple[Session, list[str]], None, None]:
    """Create a database session and clean up workflows created by a test."""
    session_factory = get_session_factory()
    session = session_factory()
    created_workflow_ids: list[str] = []

    try:
        yield session, created_workflow_ids
    finally:
        session.rollback()

        for workflow_id in created_workflow_ids:
            session.execute(
                text(
                    "DELETE FROM workflow_events "
                    "WHERE workflow_id = :workflow_id"
                ),
                {"workflow_id": workflow_id},
            )
            session.execute(
                text(
                    "DELETE FROM workflows "
                    "WHERE workflow_id = :workflow_id"
                ),
                {"workflow_id": workflow_id},
            )

        session.commit()
        session.close()


def test_database_service_persists_workflow_and_initial_events(
    database_session: tuple[Session, list[str]],
) -> None:
    """Create a workflow and verify it is persisted with initial events."""
    session, created_workflow_ids = database_session
    service = DatabaseWorkflowService(session)

    workflow = service.create_workflow(
        user_request=(
            "Please raise a dispute for TX1001. "
            "My CNIC is 12345-1234567-1."
        ),
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )
    created_workflow_ids.append(workflow.workflow_id)

    assert workflow.status == "awaiting_confirmation"
    assert workflow.requires_confirmation is True
    assert workflow.issue_type == "qr_payment_dispute"
    assert workflow.transaction_id == "TX1001"

    assert "12345-1234567-1" not in workflow.user_request
    assert "12345*******1" in workflow.user_request

    session.expire_all()

    persisted_workflow = service.get_workflow(workflow.workflow_id)
    assert persisted_workflow.workflow_id == workflow.workflow_id
    assert persisted_workflow.status == "awaiting_confirmation"
    assert "12345-1234567-1" not in persisted_workflow.user_request

    events = service.list_events(workflow.workflow_id)
    assert [event.event_type for event in events] == [
        "workflow_created",
        "confirmation_required",
    ]


def test_database_service_persists_status_transitions_and_events(
    database_session: tuple[Session, list[str]],
) -> None:
    """Confirm and complete a workflow, then verify state and audit events."""
    session, created_workflow_ids = database_session
    service = DatabaseWorkflowService(session)

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=True,
        recommended_action="create_dispute_ticket",
    )
    created_workflow_ids.append(workflow.workflow_id)

    confirmed_workflow = service.confirm_workflow(workflow.workflow_id)
    assert confirmed_workflow.status == "approved"

    completed_workflow = service.complete_workflow(
        workflow_id=workflow.workflow_id,
        dispute_ticket_id="DSP-TX1001",
    )
    assert completed_workflow.status == "completed"
    assert completed_workflow.dispute_ticket_id == "DSP-TX1001"

    session.expire_all()

    persisted_workflow = service.get_workflow(workflow.workflow_id)
    assert persisted_workflow.status == "completed"
    assert persisted_workflow.dispute_ticket_id == "DSP-TX1001"

    events = service.list_events(workflow.workflow_id)
    assert [event.event_type for event in events] == [
        "workflow_created",
        "confirmation_required",
        "user_confirmed",
        "action_completed",
    ]


def test_database_service_rejects_invalid_transition_without_new_event(
    database_session: tuple[Session, list[str]],
) -> None:
    """Invalid transitions should raise and not write misleading events."""
    session, created_workflow_ids = database_session
    service = DatabaseWorkflowService(session)

    workflow = service.create_workflow(
        user_request="Please raise a dispute for TX1001.",
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        requires_confirmation=False,
    )
    created_workflow_ids.append(workflow.workflow_id)

    with pytest.raises(InvalidWorkflowTransitionError):
        service.confirm_workflow(workflow.workflow_id)

    persisted_workflow = service.get_workflow(workflow.workflow_id)
    assert persisted_workflow.status == "created"

    events = service.list_events(workflow.workflow_id)
    assert [event.event_type for event in events] == ["workflow_created"]


def test_database_service_raises_for_unknown_workflow(
    database_session: tuple[Session, list[str]],
) -> None:
    """Unknown workflow IDs should raise the same app exception."""
    session, _created_workflow_ids = database_session
    service = DatabaseWorkflowService(session)

    with pytest.raises(WorkflowNotFoundError):
        service.get_workflow("WF-DOESNOTEXIST")