from banking_agent.routing.router import (
    classify_issue_type,
    detect_requested_action,
    extract_transaction_id,
    route_user_request,
)


def test_extract_transaction_id_returns_uppercase_id() -> None:
    transaction_id = extract_transaction_id("please check tx1001")

    assert transaction_id == "TX1001"


def test_extract_transaction_id_returns_none_when_missing() -> None:
    transaction_id = extract_transaction_id("I forgot my password")

    assert transaction_id is None


def test_classify_issue_type_qr_dispute() -> None:
    issue_type = classify_issue_type(
        "My QR payment was deducted but merchant did not receive it"
    )

    assert issue_type == "qr_payment_dispute"


def test_classify_issue_type_password_reset() -> None:
    issue_type = classify_issue_type("I forgot my mobile banking password")

    assert issue_type == "password_reset"


def test_classify_issue_type_duplicate_card_charge() -> None:
    issue_type = classify_issue_type("My card was charged twice")

    assert issue_type == "duplicate_card_charge"


def test_detect_requested_action_create_dispute() -> None:
    action = detect_requested_action("Please raise a dispute for TX1001")

    assert action == "create_dispute_ticket"


def test_route_qr_dispute_with_transaction_id() -> None:
    route = route_user_request(
        "My QR payment TX1001 was deducted but merchant did not receive it"
    )

    assert route.issue_type == "qr_payment_dispute"
    assert route.transaction_id == "TX1001"
    assert route.needs_transaction_lookup is True
    assert route.needs_policy_context is True
    assert route.needs_dispute_eligibility is True
    assert route.requires_confirmation is False


def test_route_password_reset_does_not_need_transaction_lookup() -> None:
    route = route_user_request("I forgot my mobile banking password")

    assert route.issue_type == "password_reset"
    assert route.transaction_id is None
    assert route.needs_transaction_lookup is False
    assert route.needs_dispute_eligibility is False


def test_route_create_dispute_requires_confirmation() -> None:
    route = route_user_request("Please raise a dispute for TX1001")

    assert route.requested_action == "create_dispute_ticket"
    assert route.transaction_id == "TX1001"
    assert route.needs_transaction_lookup is True
    assert route.needs_dispute_eligibility is True
    assert route.requires_confirmation is True