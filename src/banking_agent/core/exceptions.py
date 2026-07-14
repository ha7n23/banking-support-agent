class BankingAgentError(Exception):
    """Base exception for the Banking Support Agent."""


class ToolError(BankingAgentError):
    """Raised when a tool cannot complete successfully."""


class TransactionNotFoundError(ToolError):
    """Raised when a transaction ID is not found."""


class UnsupportedIssueTypeError(ToolError):
    """Raised when an issue type is not supported by the tool."""

class RoutingError(BankingAgentError):
    """Raised when a user request cannot be routed."""

class GenerationError(BankingAgentError):
    """Raised when final response generation fails."""