# Design Decisions

## 1. Controlled Agent Instead of Fully Autonomous Agent

This project uses a controlled agent design rather than letting the LLM decide and execute actions freely.

Reason:

- banking workflows require safety and predictability
- deterministic routing is easier to test
- action tools should not be executed freely by an LLM
- workflow behaviour should be explainable
- sensitive actions should require confirmation

The LLM is used only for final response generation when enabled.

## 2. Deterministic Router

The router uses Python rules to classify issue type, extract transaction IDs, and detect requested actions.

Reason:

- predictable behaviour
- easy testing
- safer for banking support workflows
- no unnecessary LLM calls for routing
- clear separation between intent detection and response writing

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

The project uses mock tools instead of real banking APIs.

Reason:

- no real customer data
- no real banking actions
- no external dependency during tests
- deterministic behaviour
- same architecture can later support real APIs

This lets the project demonstrate engineering structure without creating compliance or data-risk issues.

## 5. Read-Only vs Decision-Support vs Action Tools

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

The `create_dispute_ticket` tool only runs when action execution is confirmed.

Confirmation can happen in two ways:

```text
/support with confirm_action=true
or
/workflows/{workflow_id}/execute after a workflow is created
```

Reason:

- prevents accidental workflow actions
- mirrors real banking approval requirements
- demonstrates safe agent design
- gives the UI/API a realistic action flow

## 7. Workflow Automation Layer

A separate workflow service manages workflow state and audit events.

Reason:

- keeps agent logic separate from workflow state management
- makes support actions traceable
- enables workflow listing and inspection
- allows confirm/reject/execute/fail/complete transitions
- creates a stronger business automation pattern

The workflow service is intentionally in-memory for the portfolio project. In production, it would use persistent storage.

## 8. Audit Events

The workflow service records events for important steps.

Reason:

- banking workflows need traceability
- events help debug agent behaviour
- action execution should be auditable
- the UI can show what happened step by step

Examples:

```text
workflow_created
confirmation_required
intent_classified
tool_called
user_confirmed
action_completed
```

## 9. Deterministic and LLM-Assisted Modes

The agent supports two modes.

Deterministic mode:

```text
Python builds the final response.
```

LLM-assisted mode:

```text
Python controls tools and workflow state.
Gemini writes the final response from tool results.
```

This keeps the system safe while allowing better final response wording when an LLM is available.

## 10. No Live LLM Calls in Tests

Tests do not call Gemini.

Reason:

- no API key needed in CI
- no unpredictable output
- no API costs
- faster tests
- deterministic test results

Fake generators and deterministic paths are used to test LLM-assisted behaviour.

## 11. FastAPI Backend

FastAPI exposes the agent and workflow system through HTTP.

Reason:

- realistic application interface
- typed request and response schemas
- automatic Swagger/OpenAPI documentation
- simple testing with TestClient
- easy connection to a lightweight frontend

## 12. Lightweight FastAPI UI Instead of React

The project uses a lightweight server-served UI with Jinja2, HTML, CSS, and JavaScript.

Reason:

- no Node.js setup
- no separate frontend server
- no Docker Compose needed
- enough polish for a portfolio demo
- keeps the project focused on AI workflow engineering

A full React frontend can be saved for a larger capstone project.

## 13. Docker-Specific Runtime Requirements

The Dockerfile uses `requirements-docker.txt` instead of the full local development requirements.

Reason:

- smaller runtime dependency set
- faster Docker builds
- avoids test/dev-only packages inside the image
- cleaner production-style packaging

## 14. Docker Build Cache and Smoke Tests in CI

GitHub Actions uses Docker Buildx cache and runs a container smoke test.

Reason:

- faster CI builds after the first run
- proves the image can actually start
- checks `/health`
- checks `/ui`
- catches runtime errors that a build-only CI job could miss

## 15. Current Trade-Offs

The project is intentionally lightweight.

Trade-offs:

- workflow state is in-memory
- tools are mocked
- there is no authentication
- there is no role-based approval
- audit logs are not persisted
- UI is simple rather than a full frontend app

These choices keep the project focused and understandable while still demonstrating the core AI engineering concepts.
