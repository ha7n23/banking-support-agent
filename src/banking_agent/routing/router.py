import re

from banking_agent.core.schemas import AgentRoute, IssueType


TRANSACTION_ID_PATTERN = re.compile(r"\b(?:TX|CARD)\d{4,}\b", re.IGNORECASE)


def extract_transaction_id(user_request: str) -> str | None:
    """Extract a mock transaction ID from a user request."""
    match = TRANSACTION_ID_PATTERN.search(user_request)

    if not match:
        return None

    return match.group(0).upper()


def classify_issue_type(user_request: str) -> IssueType:
    """Classify the banking issue type using deterministic keyword rules."""
    text = user_request.lower()

    if any(word in text for word in ["password", "login", "forgot"]):
        return "password_reset"

    if any(phrase in text for phrase in ["duplicate", "charged twice", "double charge"]):
        return "duplicate_card_charge"

    if any(phrase in text for phrase in ["refund timeline", "exact refund", "how long"]):
        return "refund_timeline"

    if any(
        phrase in text
        for phrase in [
            "qr",
            "merchant did not receive",
            "merchant didn't receive",
            "deducted",
            "debit but merchant",
        ]
    ):
        return "qr_payment_dispute"

    return "general"


def detect_requested_action(user_request: str) -> str | None:
    """Detect whether the user is asking for an action."""
    text = user_request.lower()

    if any(
        phrase in text
        for phrase in [
            "raise a dispute",
            "create a dispute",
            "open a dispute",
            "submit a dispute",
            "file a dispute",
        ]
    ):
        return "create_dispute_ticket"

    return None


def route_user_request(user_request: str) -> AgentRoute:
    """Route a user request to the safe tool workflow."""
    issue_type = classify_issue_type(user_request)
    transaction_id = extract_transaction_id(user_request)
    requested_action = detect_requested_action(user_request)

    is_dispute_issue = issue_type in {
        "qr_payment_dispute",
        "duplicate_card_charge",
    }

    is_dispute_action = requested_action == "create_dispute_ticket"

    needs_transaction_lookup = (
        transaction_id is not None
        and (is_dispute_issue or is_dispute_action)
    )

    needs_dispute_eligibility = (
        transaction_id is not None
        and (is_dispute_issue or is_dispute_action)
    )

    requires_confirmation = is_dispute_action

    return AgentRoute(
        issue_type=issue_type,
        transaction_id=transaction_id,
        needs_transaction_lookup=needs_transaction_lookup,
        needs_policy_context=True,
        needs_dispute_eligibility=needs_dispute_eligibility,
        requested_action=requested_action,
        requires_confirmation=requires_confirmation,
    )