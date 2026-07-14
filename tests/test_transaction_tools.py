import pytest

from banking_agent.core.exceptions import TransactionNotFoundError
from banking_agent.tools.transaction_tools import check_transaction_status


def test_check_transaction_status_returns_qr_transaction() -> None:
    transaction = check_transaction_status("TX1001")

    assert transaction.transaction_id == "TX1001"
    assert transaction.status == "deducted"
    assert transaction.channel == "qr"
    assert transaction.merchant_received is False
    assert transaction.settlement_status == "not_settled"


def test_check_transaction_status_normalises_input() -> None:
    transaction = check_transaction_status(" tx1001 ")

    assert transaction.transaction_id == "TX1001"


def test_check_transaction_status_raises_for_missing_transaction() -> None:
    with pytest.raises(TransactionNotFoundError):
        check_transaction_status("UNKNOWN")