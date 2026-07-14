from banking_agent.services.agent_service import BankingSupportAgent


def test_agent_handles_qr_payment_dispute_with_transaction_id() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request(
        "My QR payment TX1001 was deducted but the merchant did not receive it."
    )

    assert "Transaction TX1001" in response.answer
    assert "not_settled" in response.answer
    assert "eligible for dispute support" in response.answer
    assert response.requires_confirmation is False

    tool_names = [tool_call.tool_name for tool_call in response.tool_calls]

    assert "retrieve_policy_context" in tool_names
    assert "check_transaction_status" in tool_names
    assert "check_dispute_eligibility" in tool_names


def test_agent_handles_password_reset_without_transaction_lookup() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request("I forgot my mobile banking password.")

    assert "forgot password option" in response.answer
    assert response.requires_confirmation is False

    tool_names = [tool_call.tool_name for tool_call in response.tool_calls]

    assert "retrieve_policy_context" in tool_names
    assert "check_transaction_status" not in tool_names
    assert "check_dispute_eligibility" not in tool_names


def test_agent_asks_for_transaction_id_when_specific_payment_missing_id() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request(
        "My QR payment was deducted but the merchant did not receive it."
    )

    assert "I need the transaction ID" in response.answer
    assert "QR payment disputes" in response.answer
    assert response.requires_confirmation is False


def test_agent_requires_confirmation_for_create_dispute_request() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request("Please raise a dispute for TX1001.")

    assert response.requires_confirmation is True
    assert "Transaction TX1001" in response.answer
    assert "eligible for dispute support" in response.answer
    assert "confirmation would be required" in response.answer

    tool_names = [tool_call.tool_name for tool_call in response.tool_calls]

    assert "check_transaction_status" in tool_names
    assert "retrieve_policy_context" in tool_names
    assert "check_dispute_eligibility" in tool_names


def test_agent_handles_unknown_transaction_id() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request(
        "My QR payment TX9999 was deducted but merchant did not receive it."
    )

    assert "could not find transaction ID TX9999" in response.answer
    assert response.requires_confirmation is False

class FakeTextGenerator:
    """Fake text generator for testing LLM-assisted response mode."""

    def generate(self, prompt: str) -> str:
        assert "Use only the provided tool results" in prompt
        assert "TX1001" in prompt
        return "LLM-style response based on controlled tool results."


def test_agent_can_use_text_generator_for_final_response() -> None:
    agent = BankingSupportAgent(text_generator=FakeTextGenerator())

    response = agent.handle_request(
        user_request=(
            "My QR payment TX1001 was deducted but the merchant did not receive it."
        ),
        use_llm=True,
    )

    assert response.answer == "LLM-style response based on controlled tool results."
    assert response.requires_confirmation is False

    tool_names = [tool_call.tool_name for tool_call in response.tool_calls]

    assert "check_transaction_status" in tool_names
    assert "retrieve_policy_context" in tool_names
    assert "check_dispute_eligibility" in tool_names

def test_agent_does_not_create_ticket_without_confirmation() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request("Please raise a dispute for TX1001.")

    assert response.requires_confirmation is True
    assert response.dispute_ticket is None

    tool_names = [tool_call.tool_name for tool_call in response.tool_calls]

    assert "create_dispute_ticket" not in tool_names


def test_agent_creates_ticket_when_action_confirmed() -> None:
    agent = BankingSupportAgent()

    response = agent.handle_request(
        user_request="Please raise a dispute for TX1001.",
        confirm_action=True,
    )

    assert response.requires_confirmation is False
    assert response.dispute_ticket is not None
    assert response.dispute_ticket.ticket_id == "DSP-TX1001"
    assert "mock dispute ticket has been created" in response.answer

    tool_names = [tool_call.tool_name for tool_call in response.tool_calls]

    assert "check_transaction_status" in tool_names
    assert "retrieve_policy_context" in tool_names
    assert "check_dispute_eligibility" in tool_names
    assert "create_dispute_ticket" in tool_names


def test_agent_llm_prompt_receives_created_ticket_when_confirmed() -> None:
    class FakeTicketAwareTextGenerator:
        """Fake generator that checks created ticket context is in the prompt."""

        def generate(self, prompt: str) -> str:
            assert "Action tool result:" in prompt
            assert "Ticket ID: DSP-TX1001" in prompt
            assert "Status: created" in prompt
            return "A dispute ticket has been created after confirmation."

    agent = BankingSupportAgent(text_generator=FakeTicketAwareTextGenerator())

    response = agent.handle_request(
        user_request="Please raise a dispute for TX1001.",
        use_llm=True,
        confirm_action=True,
    )

    assert response.answer == "A dispute ticket has been created after confirmation."
    assert response.requires_confirmation is False
    assert response.dispute_ticket is not None
    assert response.dispute_ticket.ticket_id == "DSP-TX1001" 