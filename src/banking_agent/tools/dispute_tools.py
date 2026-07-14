from banking_agent.core.exceptions import UnsupportedIssueTypeError
from banking_agent.core.schemas import (
    DisputeEligibility,
    IssueType,
    TransactionStatus,
)


def check_dispute_eligibility(
    transaction: TransactionStatus,
    issue_type: IssueType,
) -> DisputeEligibility:
    """Check whether a mock transaction appears eligible for dispute support."""
    if issue_type == "qr_payment_dispute":
        eligible = (
            transaction.channel == "qr"
            and transaction.status in {"deducted", "failed", "pending"}
            and transaction.merchant_received is False
        )

        if eligible:
            return DisputeEligibility(
                transaction_id=transaction.transaction_id,
                issue_type=issue_type,
                eligible=True,
                reason=(
                    "The transaction appears to involve a QR payment where the "
                    "customer was debited but merchant receipt is not confirmed."
                ),
                requires_human_review=True,
            )

        return DisputeEligibility(
            transaction_id=transaction.transaction_id,
            issue_type=issue_type,
            eligible=False,
            reason=(
                "The transaction does not match the QR payment dispute conditions "
                "used by this mock eligibility tool."
            ),
            requires_human_review=False,
        )

    if issue_type == "duplicate_card_charge":
        eligible = (
            transaction.channel == "card"
            and transaction.status == "duplicate_charge"
        )

        if eligible:
            return DisputeEligibility(
                transaction_id=transaction.transaction_id,
                issue_type=issue_type,
                eligible=True,
                reason=(
                    "The transaction appears to be a duplicate card charge and "
                    "can be reviewed through the dispute process."
                ),
                requires_human_review=True,
            )

        return DisputeEligibility(
            transaction_id=transaction.transaction_id,
            issue_type=issue_type,
            eligible=False,
            reason=(
                "The transaction does not match the duplicate card charge "
                "conditions used by this mock eligibility tool."
            ),
            requires_human_review=False,
        )

    raise UnsupportedIssueTypeError(
        f"Dispute eligibility is not supported for issue type '{issue_type}'."
    )