# Design Decisions

## 1. Controlled Agent Instead of Fully Autonomous Agent

This project uses a controlled hybrid agent design.

Reason:

- banking workflows require safety and predictability
- deterministic routing is easier to test
- action tools should not be executed freely by an LLM
- tool behaviour should be explainable

The LLM is used only for final response generation when enabled.

## 2. Deterministic Router

The router uses Python rules to classify issue type, extract transaction IDs, and detect requested actions.

Reason:

- predictable behaviour
- easy testing
- safer for banking support workflows
- no unnecessary LLM calls for routing

## 3. Typed Tool Results

Tools return Pydantic models instead of raw dictionaries.

Reason:

- validation
- type safety
- clearer interfaces
- easier tests
- less fragile agent logic

Example models:

```text
TransactionStatus
PolicyContext
DisputeEligibility
DisputeTicket
```

## 4. Mock Tools First

The project uses mock tools instead of real APIs.

Reason:

- no real customer data
- no real banking actions
- no external dependency during tests
- deterministic behaviour
- same architecture can later support real APIs

## 5. Read-Only vs Action Tool Separation

The project separates tools by risk level.

Read-only tools:

```text
check_transaction_status
retrieve_policy_context
```

Decision-support tools:

```text
check_dispute_eligibility
```

Action tools:

```text
create_dispute_ticket
```

Action tools require confirmation.

## 6. Confirmation-Gated Actions

The `create_dispute_ticket` tool only runs when `confirm_action=True`.

Reason:

- prevents accidental workflow creation
- mirrors real banking approval requirements
- demonstrates safe agent design

## 7. Deterministic and LLM-Assisted Modes

The agent supports two modes.

Deterministic mode:

```text
Python builds the final response.
```

LLM-assisted mode:

```text
Python controls tools.
Gemini writes the final response from tool results.
```

This keeps the system safe while improving response quality.

## 8. No Live LLM Calls in Tests

Tests do not call Gemini.

Reason:

- no API key needed in CI
- no unpredictable output
- no API costs
- faster tests

Fake generators are used to test LLM-assisted behaviour.

## 9. FastAPI Backend

FastAPI exposes the agent through an API.

Reason:

- realistic application interface
- easy Swagger documentation
- useful for frontend or internal tool integration
- simple testing with TestClient

## 10. Docker and CI

Docker provides a portable runtime.

GitHub Actions validates:

```text
pytest
docker build
```

Reason:

- consistent execution
- stronger portfolio credibility
- catches test or build failures early