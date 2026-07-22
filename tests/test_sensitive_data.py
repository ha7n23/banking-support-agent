from banking_agent.security.sensitive_data import mask_sensitive_text


def test_mask_sensitive_text_masks_plain_cnic() -> None:
    text = "My CNIC is 4220112345678."

    masked_text = mask_sensitive_text(text)

    assert "4220112345678" not in masked_text
    assert "42201*******8" in masked_text


def test_mask_sensitive_text_masks_hyphenated_cnic() -> None:
    text = "Customer CNIC: 42201-1234567-8."

    masked_text = mask_sensitive_text(text)

    assert "42201-1234567-8" not in masked_text
    assert "42201*******8" in masked_text


def test_mask_sensitive_text_masks_card_number() -> None:
    text = "Card number is 4567 1234 1234 9876."

    masked_text = mask_sensitive_text(text)

    assert "4567 1234 1234 9876" not in masked_text
    assert "**** **** **** 9876" in masked_text


def test_mask_sensitive_text_masks_long_account_like_number() -> None:
    text = "Account number 123456789012345 should not appear in logs."

    masked_text = mask_sensitive_text(text)

    assert "123456789012345" not in masked_text
    assert "12*********2345" in masked_text


def test_mask_sensitive_text_leaves_short_transaction_id_unchanged() -> None:
    text = "Please raise a dispute for TX1001."

    masked_text = mask_sensitive_text(text)

    assert masked_text == text


def test_mask_sensitive_text_handles_multiple_sensitive_values() -> None:
    text = (
        "CNIC 4220112345678, card 4567123412349876, "
        "account 123456789012345."
    )

    masked_text = mask_sensitive_text(text)

    assert "4220112345678" not in masked_text
    assert "4567123412349876" not in masked_text
    assert "123456789012345" not in masked_text
    assert "42201*******8" in masked_text
    assert "**** **** **** 9876" in masked_text