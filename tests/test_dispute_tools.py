import pytest

from banking_agent.core.exceptions import UnsupportedIssueTypeError
from banking_agent.tools.dispute_tools import check_dispute_eligibility
from banking_agent.tools.transaction_tools import check_transaction_status


def test_qr_payment_dispute_is_eligible_when_merchant_not_received() -> None:
    transaction = check_transaction_status("TX1001")

    eligibility = check_dispute_eligibility(
        transaction=transaction,
        issue_type="qr_payment_dispute",
    )

    assert eligibility.eligible is True
    assert eligibility.requires_human_review is True
    assert "merchant receipt is not confirmed" in eligibility.reason


def test_successful_qr_payment_is_not_eligible_for_qr_dispute() -> None:
    transaction = check_transaction_status("TX1002")

    eligibility = check_dispute_eligibility(
        transaction=transaction,
        issue_type="qr_payment_dispute",
    )

    assert eligibility.eligible is False
    assert eligibility.requires_human_review is False


def test_duplicate_card_charge_is_eligible() -> None:
    transaction = check_transaction_status("CARD2002")

    eligibility = check_dispute_eligibility(
        transaction=transaction,
        issue_type="duplicate_card_charge",
    )

    assert eligibility.eligible is True
    assert eligibility.requires_human_review is True


def test_unsupported_issue_type_raises_error() -> None:
    transaction = check_transaction_status("TX1001")

    with pytest.raises(UnsupportedIssueTypeError):
        check_dispute_eligibility(
            transaction=transaction,
            issue_type="password_reset",
        )