from banking_agent.core.exceptions import TransactionNotFoundError
from banking_agent.core.schemas import TransactionStatus


MOCK_TRANSACTIONS: dict[str, TransactionStatus] = {
    "TX1001": TransactionStatus(
        transaction_id="TX1001",
        status="deducted",
        channel="qr",
        amount=2500.0,
        merchant_received=False,
        settlement_status="not_settled",
    ),
    "TX1002": TransactionStatus(
        transaction_id="TX1002",
        status="successful",
        channel="qr",
        amount=1200.0,
        merchant_received=True,
        settlement_status="settled",
    ),
    "TX1003": TransactionStatus(
        transaction_id="TX1003",
        status="pending",
        channel="qr",
        amount=3000.0,
        merchant_received=False,
        settlement_status="pending",
    ),
    "CARD2002": TransactionStatus(
        transaction_id="CARD2002",
        status="duplicate_charge",
        channel="card",
        amount=4500.0,
        merchant_received=True,
        settlement_status="settled",
    ),
}


def check_transaction_status(transaction_id: str) -> TransactionStatus:
    """Check the status of a mock banking transaction."""
    cleaned_id = transaction_id.strip().upper()

    if cleaned_id not in MOCK_TRANSACTIONS:
        raise TransactionNotFoundError(
            f"Transaction ID '{transaction_id}' was not found."
        )

    return MOCK_TRANSACTIONS[cleaned_id]