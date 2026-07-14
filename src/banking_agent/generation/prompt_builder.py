from banking_agent.core.schemas import (
    AgentRoute,
    DisputeEligibility,
    DisputeTicket,
    PolicyContext,
    TransactionStatus,
)


def format_transaction_context(transaction: TransactionStatus | None) -> str:
    """Format transaction status for the LLM prompt."""
    if transaction is None:
        return "No transaction status was available."

    return (
        f"Transaction ID: {transaction.transaction_id}\n"
        f"Status: {transaction.status}\n"
        f"Channel: {transaction.channel}\n"
        f"Amount: {transaction.amount}\n"
        f"Merchant received: {transaction.merchant_received}\n"
        f"Settlement status: {transaction.settlement_status}"
    )


def format_eligibility_context(eligibility: DisputeEligibility | None) -> str:
    """Format dispute eligibility result for the LLM prompt."""
    if eligibility is None:
        return "No dispute eligibility check was performed."

    return (
        f"Eligible: {eligibility.eligible}\n"
        f"Reason: {eligibility.reason}\n"
        f"Requires human review: {eligibility.requires_human_review}"
    )

def format_action_context(dispute_ticket: DisputeTicket | None) -> str:
    """Format action tool result for the LLM prompt."""
    if dispute_ticket is None:
        return "No dispute ticket was created."

    return (
        f"Ticket ID: {dispute_ticket.ticket_id}\n"
        f"Transaction ID: {dispute_ticket.transaction_id}\n"
        f"Issue type: {dispute_ticket.issue_type}\n"
        f"Status: {dispute_ticket.status}\n"
        f"Summary: {dispute_ticket.summary}\n"
        f"Requires human review: {dispute_ticket.requires_human_review}"
    )

def build_agent_response_prompt(
    user_request: str,
    route: AgentRoute,
    policy_context: PolicyContext,
    transaction: TransactionStatus | None,
    eligibility: DisputeEligibility | None,
    dispute_ticket: DisputeTicket | None = None,
) -> str:
    """Build a safe prompt for generating a customer-facing agent response."""
    transaction_context = format_transaction_context(transaction)
    eligibility_context = format_eligibility_context(eligibility)
    action_context = format_action_context(dispute_ticket)

    return f"""
You are a cautious banking support assistant.

Write a clear, professional response to the customer using only the provided tool results.

Rules:
- Use only the provided tool results.
- Do not invent refund timelines, fees, limits, guarantees, or policy details.
- Do not claim that a dispute ticket has been created unless the action tool result contains a created ticket.
- If the user asks to raise/create/file a dispute and no ticket was created, explain that confirmation is required before any ticket is created.
- If no transaction status is available for a payment-specific issue, ask the customer for the transaction ID.
- Keep the response concise and helpful.
- Mention the source policy section when useful.

User request:
{user_request}

Routing decision:
Issue type: {route.issue_type}
Transaction ID: {route.transaction_id}
Requested action: {route.requested_action}
Requires confirmation: {route.requires_confirmation}

Transaction tool result:
{transaction_context}

Policy tool result:
Source: {policy_context.source}
Section: {policy_context.section}
Summary: {policy_context.summary}

Dispute eligibility tool result:
{eligibility_context}

Action tool result:
{action_context}

Final customer response:
""".strip()