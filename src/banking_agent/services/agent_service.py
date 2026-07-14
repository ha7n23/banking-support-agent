from banking_agent.core.exceptions import (
    TransactionNotFoundError,
    UnsupportedIssueTypeError,
)
from banking_agent.core.schemas import (
    AgentResponse,
    AgentRoute,
    DisputeEligibility,
    IssueType,
    PolicyContext,
    ToolCallRecord,
    TransactionStatus,
)
from banking_agent.routing.router import route_user_request
from banking_agent.tools.dispute_tools import check_dispute_eligibility
from banking_agent.tools.policy_tools import retrieve_policy_context
from banking_agent.tools.transaction_tools import check_transaction_status


class BankingSupportAgent:
    """Controlled banking support agent using deterministic routing and tools."""

    def handle_request(self, user_request: str) -> AgentResponse:
        """Handle a user request using safe tool routing."""
        route = route_user_request(user_request)
        tool_calls: list[ToolCallRecord] = []

        transaction: TransactionStatus | None = None
        eligibility: DisputeEligibility | None = None

        if route.needs_transaction_lookup and route.transaction_id:
            try:
                transaction = check_transaction_status(route.transaction_id)
                tool_calls.append(
                    ToolCallRecord(
                        tool_name="check_transaction_status",
                        input_summary=f"transaction_id={route.transaction_id}",
                        output_summary=(
                            f"status={transaction.status}, "
                            f"settlement={transaction.settlement_status}"
                        ),
                    )
                )
            except TransactionNotFoundError:
                return AgentResponse(
                    user_request=user_request,
                    answer=(
                        f"I could not find transaction ID {route.transaction_id}. "
                        "Please check the transaction ID and try again."
                    ),
                    tool_calls=tool_calls,
                    requires_confirmation=False,
                )

        effective_issue_type = self._infer_issue_type_from_transaction(
            route=route,
            transaction=transaction,
        )

        policy_context = retrieve_policy_context(effective_issue_type)
        tool_calls.append(
            ToolCallRecord(
                tool_name="retrieve_policy_context",
                input_summary=f"issue_type={effective_issue_type}",
                output_summary=f"{policy_context.source} / {policy_context.section}",
            )
        )

        if route.needs_dispute_eligibility and transaction is not None:
            try:
                eligibility = check_dispute_eligibility(
                    transaction=transaction,
                    issue_type=effective_issue_type,
                )
                tool_calls.append(
                    ToolCallRecord(
                        tool_name="check_dispute_eligibility",
                        input_summary=(
                            f"transaction_id={transaction.transaction_id}, "
                            f"issue_type={effective_issue_type}"
                        ),
                        output_summary=(
                            f"eligible={eligibility.eligible}, "
                            f"human_review={eligibility.requires_human_review}"
                      ),
                    )
                )
            except UnsupportedIssueTypeError:
                eligibility = None

        effective_route = route.model_copy(
            update={"issue_type": effective_issue_type}
        )

        answer = self._build_answer(
            route=effective_route,
            policy_context=policy_context,
            transaction=transaction,
            eligibility=eligibility,
        )

        return AgentResponse(
            user_request=user_request,
            answer=answer,
            tool_calls=tool_calls,
            requires_confirmation=route.requires_confirmation,
        )


    def _build_answer(
        self,
        route: AgentRoute,
        policy_context: PolicyContext,
        transaction: TransactionStatus | None,
        eligibility: DisputeEligibility | None,
    ) -> str:
        """Build a deterministic support response from route and tool results."""
        parts: list[str] = []

        if transaction is not None:
            parts.append(
                f"Transaction {transaction.transaction_id} is marked as "
                f"{transaction.status}. Settlement status is "
                f"{transaction.settlement_status}."
            )

            if transaction.merchant_received is not None:
                merchant_status = (
                    "confirmed by the merchant"
                    if transaction.merchant_received
                    else "not confirmed by the merchant"
                )
                parts.append(f"Merchant receipt is {merchant_status}.")

        elif route.issue_type in {"qr_payment_dispute", "duplicate_card_charge"}:
            parts.append(
                "I can give general guidance, but I need the transaction ID "
                "to check the specific transaction status."
            )

        parts.append(policy_context.summary)

        if eligibility is not None:
            if eligibility.eligible:
                parts.append(
                    "Based on the mock eligibility check, this case appears "
                    "eligible for dispute support."
                )
            else:
                parts.append(
                    "Based on the mock eligibility check, this case does not "
                    "currently match the dispute conditions."
                )

            parts.append(eligibility.reason)

        if route.issue_type == "refund_timeline":
            parts.append(
                "I cannot confirm an exact refund timeline from the available "
                "policy context."
            )

        if route.requires_confirmation:
            parts.append(
                "You asked to create or raise a dispute. This would be an action, "
                "so confirmation would be required before creating any ticket."
            )

        return " ".join(parts)
    
    def _infer_issue_type_from_transaction(
        self,
        route: AgentRoute,
        transaction: TransactionStatus | None,
    ) -> IssueType:
        """Infer a more specific issue type from transaction data when needed."""
        if route.issue_type != "general":
            return route.issue_type

        if transaction is None:
            return route.issue_type

        if route.requested_action == "create_dispute_ticket":
            if transaction.channel == "qr":
                return "qr_payment_dispute"

            if transaction.channel == "card":
                return "duplicate_card_charge"

        return route.issue_type