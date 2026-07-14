from fastapi.testclient import TestClient

from banking_agent.api.app import app
from banking_agent.api.dependencies import get_agent_factory
from banking_agent.core.schemas import (
    AgentResponse,
    DisputeTicket,
    ToolCallRecord,
)


class FakeAgent:
    """Fake agent used for API tests."""

    def handle_request(
        self,
        user_request: str,
        use_llm: bool = False,
        confirm_action: bool = False,
    ) -> AgentResponse:
        tool_calls = [
            ToolCallRecord(
                tool_name="check_transaction_status",
                input_summary="transaction_id=TX1001",
                output_summary="status=deducted, settlement=not_settled",
            )
        ]

        dispute_ticket = None
        requires_confirmation = False

        if "raise a dispute" in user_request.lower() and not confirm_action:
            requires_confirmation = True

        if confirm_action:
            dispute_ticket = DisputeTicket(
                ticket_id="DSP-TX1001",
                transaction_id="TX1001",
                issue_type="qr_payment_dispute",
                status="created",
                summary="Mock dispute ticket created.",
                requires_human_review=True,
            )

        return AgentResponse(
            user_request=user_request,
            answer="Fake agent response.",
            tool_calls=tool_calls,
            requires_confirmation=requires_confirmation,
            dispute_ticket=dispute_ticket,
        )


def fake_agent_factory(use_llm: bool) -> FakeAgent:
    """Return fake agent for tests."""
    return FakeAgent()


client = TestClient(app)


def setup_module() -> None:
    """Override agent factory dependency."""
    app.dependency_overrides[get_agent_factory] = lambda: fake_agent_factory


def teardown_module() -> None:
    """Clear dependency overrides."""
    app.dependency_overrides.clear()


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "app_name" in data
    assert "environment" in data


def test_support_endpoint_returns_agent_response() -> None:
    response = client.post(
        "/support",
        json={
            "user_request": "My QR payment TX1001 was deducted.",
            "use_llm": False,
            "confirm_action": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_request"] == "My QR payment TX1001 was deducted."
    assert data["answer"] == "Fake agent response."
    assert len(data["tool_calls"]) == 1
    assert data["requires_confirmation"] is False
    assert data["dispute_ticket"] is None


def test_support_endpoint_requires_confirmation_for_action_request() -> None:
    response = client.post(
        "/support",
        json={
            "user_request": "Please raise a dispute for TX1001.",
            "use_llm": False,
            "confirm_action": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["requires_confirmation"] is True
    assert data["dispute_ticket"] is None


def test_support_endpoint_returns_ticket_when_action_confirmed() -> None:
    response = client.post(
        "/support",
        json={
            "user_request": "Please raise a dispute for TX1001.",
            "use_llm": False,
            "confirm_action": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["requires_confirmation"] is False
    assert data["dispute_ticket"]["ticket_id"] == "DSP-TX1001"
    assert data["dispute_ticket"]["status"] == "created"


def test_support_endpoint_rejects_empty_request() -> None:
    response = client.post(
        "/support",
        json={
            "user_request": "",
            "use_llm": False,
            "confirm_action": False,
        },
    )

    assert response.status_code == 422