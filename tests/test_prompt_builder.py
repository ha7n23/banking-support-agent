from banking_agent.core.schemas import (
    AgentRoute,
    DisputeEligibility,
    PolicyContext,
    TransactionStatus,
)
from banking_agent.generation.prompt_builder import build_agent_response_prompt


def test_build_agent_response_prompt_includes_tool_results() -> None:
    route = AgentRoute(
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        needs_transaction_lookup=True,
        needs_policy_context=True,
        needs_dispute_eligibility=True,
        requested_action=None,
        requires_confirmation=False,
    )

    transaction = TransactionStatus(
        transaction_id="TX1001",
        status="deducted",
        channel="qr",
        amount=2500.0,
        merchant_received=False,
        settlement_status="not_settled",
    )

    policy_context = PolicyContext(
        issue_type="qr_payment_dispute",
        summary="The bank reviews transaction status and settlement records.",
        source="digital_payments_policy.md",
        section="QR Payment Disputes",
    )

    eligibility = DisputeEligibility(
        transaction_id="TX1001",
        issue_type="qr_payment_dispute",
        eligible=True,
        reason="Merchant receipt is not confirmed.",
        requires_human_review=True,
    )

    prompt = build_agent_response_prompt(
        user_request="My QR payment TX1001 failed.",
        route=route,
        policy_context=policy_context,
        transaction=transaction,
        eligibility=eligibility,
    )

    assert "Use only the provided tool results" in prompt
    assert "TX1001" in prompt
    assert "not_settled" in prompt
    assert "QR Payment Disputes" in prompt
    assert "Merchant receipt is not confirmed" in prompt


def test_build_agent_response_prompt_includes_confirmation_rule() -> None:
    route = AgentRoute(
        issue_type="qr_payment_dispute",
        transaction_id="TX1001",
        needs_transaction_lookup=True,
        needs_policy_context=True,
        needs_dispute_eligibility=True,
        requested_action="create_dispute_ticket",
        requires_confirmation=True,
    )

    policy_context = PolicyContext(
        issue_type="qr_payment_dispute",
        summary="QR disputes require review.",
        source="digital_payments_policy.md",
        section="QR Payment Disputes",
    )

    prompt = build_agent_response_prompt(
        user_request="Please raise a dispute for TX1001.",
        route=route,
        policy_context=policy_context,
        transaction=None,
        eligibility=None,
    )

    assert "Do not claim that a dispute ticket has been created" in prompt
    assert "confirmation is required" in prompt
    assert "Requires confirmation: True" in prompt