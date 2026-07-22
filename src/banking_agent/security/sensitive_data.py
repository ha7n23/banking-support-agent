import re


CNIC_PATTERN = re.compile(r"\b(\d{5})[- ]?(\d{7})[- ]?(\d{1})\b")

CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[ -]){3}\d{4}\b|\b\d{16}\b"
)

LONG_NUMBER_PATTERN = re.compile(r"\b\d{10,24}\b")


def mask_cnic(match: re.Match[str]) -> str:
    """Mask a Pakistani CNIC-like identifier."""
    first_group = match.group(1)
    middle_group = match.group(2)
    last_group = match.group(3)

    return f"{first_group}{'*' * len(middle_group)}{last_group}"


def mask_card_number(match: re.Match[str]) -> str:
    """Mask a card-like number while keeping only the final four digits."""
    raw_value = match.group(0)
    digits = re.sub(r"\D", "", raw_value)

    if len(digits) < 13 or len(digits) > 19:
        return raw_value

    return f"**** **** **** {digits[-4:]}"


def mask_long_number(match: re.Match[str]) -> str:
    """
    Mask long account/session/reference-like numbers.

    CNIC and card numbers are handled before this generic rule.
    """
    value = match.group(0)

    if len(value) <= 6:
        return value

    return f"{value[:2]}{'*' * (len(value) - 6)}{value[-4:]}"


def mask_sensitive_text(text: str) -> str:
    """
    Mask common sensitive identifiers from free text.

    This helper is intentionally lightweight. It demonstrates privacy-conscious
    handling for a mock portfolio project and should not be treated as a full
    enterprise PII detection system.
    """
    masked_text = CNIC_PATTERN.sub(mask_cnic, text)
    masked_text = CARD_PATTERN.sub(mask_card_number, masked_text)
    masked_text = LONG_NUMBER_PATTERN.sub(mask_long_number, masked_text)

    return masked_text