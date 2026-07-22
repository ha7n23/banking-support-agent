from dataclasses import dataclass
from typing import Literal


RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class PromptSafetyResult:
    """Result of a lightweight prompt safety check."""

    is_allowed: bool
    risk_level: RiskLevel
    flags: list[str]
    safe_message: str | None = None


UNSAFE_PATTERNS: dict[str, tuple[str, ...]] = {
    "prompt_injection": (
        "ignore previous instructions",
        "ignore all previous instructions",
        "ignore your instructions",
        "ignore the system prompt",
        "override your instructions",
        "developer mode",
        "jailbreak",
    ),
    "bypass_confirmation": (
        "bypass confirmation",
        "skip confirmation",
        "without confirmation",
        "no confirmation required",
        "do not ask for confirmation",
        "don't ask for confirmation",
        "i already confirmed",
        "confirmed=true",
    ),
    "disable_audit_logging": (
        "do not log",
        "don't log",
        "without logging",
        "hide this action",
        "do not record",
        "don't record",
        "no audit",
        "disable audit",
    ),
    "system_prompt_leakage": (
        "system prompt",
        "hidden instructions",
        "developer message",
        "show system prompt",
        "print system prompt",
        "reveal system prompt",
        "show hidden instructions",
        "reveal hidden instructions",
        "print hidden instructions",
        "show developer message",
        "reveal developer message",
    ),
}


SAFE_FALLBACK_MESSAGE = (
    "I cannot bypass confirmation, audit logging, workflow controls, "
    "or reveal hidden system instructions. I can help through the normal "
    "support workflow using the allowed safety controls."
)


def normalize_text(text: str) -> str:
    """Normalise text for lightweight phrase matching."""
    return " ".join(text.lower().split())


def check_prompt_safety(user_request: str) -> PromptSafetyResult:
    """
    Check whether a user request contains obvious unsafe instruction patterns.

    This is a lightweight portfolio-grade guardrail. It is not a complete
    security classifier, but it demonstrates application-layer defence against
    direct prompt injection attempts.
    """
    normalized_request = normalize_text(user_request)
    flags: list[str] = []

    for flag, patterns in UNSAFE_PATTERNS.items():
        if any(pattern in normalized_request for pattern in patterns):
            flags.append(flag)

    if not flags:
        return PromptSafetyResult(
            is_allowed=True,
            risk_level="low",
            flags=[],
        )

    return PromptSafetyResult(
        is_allowed=False,
        risk_level="high",
        flags=flags,
        safe_message=SAFE_FALLBACK_MESSAGE,
    )