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