from banking_agent.core.exceptions import (
    ActionRequiresConfirmationError,
    DisputeNotEligibleError,
)
from banking_agent.core.schemas import (
    DisputeEligibility,
    DisputeTicket,
    TransactionStatus,
)


def create_dispute_ticket(
    transaction: TransactionStatus,
    eligibility: DisputeEligibility,
    customer_confirmed: bool,
) -> DisputeTicket:
    """Create a mock dispute ticket only after explicit confirmation."""
    if not customer_confirmed:
        raise ActionRequiresConfirmationError(
            "Customer confirmation is required before creating a dispute ticket."
        )

    if not eligibility.eligible:
        raise DisputeNotEligibleError(
            "A dispute ticket cannot be created because the case is not eligible."
        )

    ticket_id = f"DSP-{transaction.transaction_id}"

    return DisputeTicket(
        ticket_id=ticket_id,
        transaction_id=transaction.transaction_id,
        issue_type=eligibility.issue_type,
        status="created",
        summary=(
            f"Mock dispute ticket created for {transaction.transaction_id}. "
            f"Reason: {eligibility.reason}"
        ),
        requires_human_review=eligibility.requires_human_review,
    )