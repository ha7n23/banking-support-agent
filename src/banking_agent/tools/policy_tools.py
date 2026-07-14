from banking_agent.core.schemas import IssueType, PolicyContext


POLICY_CONTEXTS: dict[IssueType, PolicyContext] = {
    "qr_payment_dispute": PolicyContext(
        issue_type="qr_payment_dispute",
        summary=(
            "For QR payment disputes where the customer was debited but the "
            "merchant did not receive confirmation, the bank reviews transaction "
            "status, merchant confirmation, settlement records, and channel logs."
        ),
        source="digital_payments_policy.md",
        section="QR Payment Disputes",
    ),
    "duplicate_card_charge": PolicyContext(
        issue_type="duplicate_card_charge",
        summary=(
            "Duplicate card charge cases can be reported for investigation. "
            "The bank may review card transaction logs, merchant records, and "
            "settlement information."
        ),
        source="card_disputes_policy.md",
        section="Duplicate Card Charges",
    ),
    "password_reset": PolicyContext(
        issue_type="password_reset",
        summary=(
            "Customers who forget their mobile banking password should use the "
            "forgot password option in the mobile app and verify their registered "
            "mobile number."
        ),
        source="mobile_app_policy.md",
        section="Password Recovery",
    ),
    "refund_timeline": PolicyContext(
        issue_type="refund_timeline",
        summary=(
            "The available policy context does not specify an exact refund "
            "timeline. The customer should be told that no exact timeline is "
            "available from the provided context."
        ),
        source="digital_payments_policy.md",
        section="Refund Timeline",
    ),
    "general": PolicyContext(
        issue_type="general",
        summary=(
            "For general banking support issues, the customer should be guided "
            "towards the relevant official support channel."
        ),
        source="general_support_policy.md",
        section="General Support",
    ),
}


def retrieve_policy_context(issue_type: IssueType) -> PolicyContext:
    """Retrieve mock policy context for a banking support issue."""
    return POLICY_CONTEXTS[issue_type]