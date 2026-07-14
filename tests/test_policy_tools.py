from banking_agent.tools.policy_tools import retrieve_policy_context


def test_retrieve_policy_context_for_qr_dispute() -> None:
    policy = retrieve_policy_context("qr_payment_dispute")

    assert policy.issue_type == "qr_payment_dispute"
    assert policy.section == "QR Payment Disputes"
    assert "merchant" in policy.summary.lower()


def test_retrieve_policy_context_for_password_reset() -> None:
    policy = retrieve_policy_context("password_reset")

    assert policy.issue_type == "password_reset"
    assert "forgot password" in policy.summary.lower()
    assert policy.section == "Password Recovery"