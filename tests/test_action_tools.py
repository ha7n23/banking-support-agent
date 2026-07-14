import pytest

from banking_agent.core.exceptions import (
    ActionRequiresConfirmationError,
    DisputeNotEligibleError,
)
from banking_agent.core.schemas import DisputeEligibility
from banking_agent.tools.action_tools import create_dispute_ticket
from banking_agent.tools.dispute_tools import check_dispute_eligibility
from banking_agent.tools.transaction_tools import check_transaction_status


def test_create_dispute_ticket_requires_confirmation() -> None:
    transaction = check_transaction_status("TX1001")
    eligibility = check_dispute_eligibility(
        transaction=transaction,
        issue_type="qr_payment_dispute",
    )

    with pytest.raises(ActionRequiresConfirmationError):
        create_dispute_ticket(
            transaction=transaction,
            eligibility=eligibility,
            customer_confirmed=False,
        )


def test_create_dispute_ticket_creates_ticket_when_confirmed() -> None:
    transaction = check_transaction_status("TX1001")
    eligibility = check_dispute_eligibility(
        transaction=transaction,
        issue_type="qr_payment_dispute",
    )

    ticket = create_dispute_ticket(
        transaction=transaction,
        eligibility=eligibility,
        customer_confirmed=True,
    )

    assert ticket.ticket_id == "DSP-TX1001"
    assert ticket.transaction_id == "TX1001"
    assert ticket.issue_type == "qr_payment_dispute"
    assert ticket.status == "created"
    assert ticket.requires_human_review is True


def test_create_dispute_ticket_rejects_ineligible_case() -> None:
    transaction = check_transaction_status("TX1002")
    eligibility = DisputeEligibility(
        transaction_id="TX1002",
        issue_type="qr_payment_dispute",
        eligible=False,
        reason="Successful settled QR payment is not eligible in this mock rule.",
        requires_human_review=False,
    )

    with pytest.raises(DisputeNotEligibleError):
        create_dispute_ticket(
            transaction=transaction,
            eligibility=eligibility,
            customer_confirmed=True,
        )