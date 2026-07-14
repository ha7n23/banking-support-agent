from argparse import ArgumentParser

from banking_agent.services.agent_service import BankingSupportAgent


DEFAULT_REQUEST = (
    "My QR payment TX1001 was deducted but the merchant did not receive it. "
    "What should I do?"
)


def parse_args() -> ArgumentParser:
    """Create command-line argument parser."""
    parser = ArgumentParser(
        description="Run the controlled banking support agent."
    )

    parser.add_argument(
        "--request",
        type=str,
        default=DEFAULT_REQUEST,
        help="User banking support request.",
    )

    return parser


def main() -> None:
    """Run the banking support agent for a user request."""
    parser = parse_args()
    args = parser.parse_args()

    agent = BankingSupportAgent()
    response = agent.handle_request(args.request)

    print("\n" + "=" * 80)
    print("USER REQUEST")
    print("=" * 80)
    print(response.user_request)

    print("\n" + "=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(response.answer)

    print("\n" + "=" * 80)
    print("TOOL CALLS")
    print("=" * 80)

    for index, tool_call in enumerate(response.tool_calls, start=1):
        print(f"{index}. {tool_call.tool_name}")
        print(f"   Input: {tool_call.input_summary}")
        print(f"   Output: {tool_call.output_summary}")

    print("\n" + "=" * 80)
    print("REQUIRES CONFIRMATION")
    print("=" * 80)
    print(response.requires_confirmation)


if __name__ == "__main__":
    main()