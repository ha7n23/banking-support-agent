# Design Decisions

## 1. Controlled Agent Instead of Fully Autonomous Agent

This project uses a controlled agent design rather than letting the LLM decide and execute actions freely.

Reason:

- banking workflows require safety and predictability,
- deterministic behaviour is easier to test,
- action tools should not be executed directly by a model,
- workflow behaviour should be explainable,
- sensitive actions should require confirmation.

The LLM is used only for final response generation when enabled.

## 2. Deterministic Router

The router uses Python rules to classify issue type, extract transaction IDs, and detect requested actions.

Reason:

- predictable behaviour,
- safer handling of banking-style requests,
- no unnecessary LLM calls for routing,
- easier unit testing,
- clear separation between intent detection and response writing.

## 3. Typed Tool Results

Tools return Pydantic models instead of raw dictionaries.

Reason:

- validation,
- type safety,
- clearer interfaces,
- easier tests,
- less fragile agent logic.

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

- no real customer data,
- no real banking actions,
- no dependency on external banking systems,
- deterministic test behaviour,
- safe demonstration of the architecture.

This allows the project to show engineering structure without creating compliance or data-risk issues.

## 5. Read-Only, Decision-Support, and Action Tools

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

Read-only and decision-support tools can run automatically. Action tools require confirmation.

## 6. Confirmation-Gated Actions

Creating a dispute ticket is treated as a state-changing action.

The app can investigate a case and explain the result without confirmation. It only creates a mock dispute ticket when confirmation is present or an approved workflow is executed.

Reason:

- prevents accidental action execution,
- mirrors approval requirements in real support workflows,
- creates a clear boundary between guidance and action,
- makes the system safer to demo and test.

## 7. Workflow Automation Layer

The workflow layer was added so action-oriented requests are tracked beyond a single response.

A workflow can record:

```text
workflow_id
issue_type
transaction_id
status
recommended_action
confirmation requirement
dispute_ticket_id
timestamps
failure reason
```

Reason:

- support actions need state,
- users may need to confirm later,
- actions need traceability,
- the UI/API can show the workflow lifecycle,
- testing can validate status transitions.

## 8. Audit Events

Workflow events record what happened during a workflow.

Examples:

```text
workflow_created
intent_classified
tool_called
confirmation_required
user_confirmed
action_completed
action_rejected
workflow_failed
```

Reason:

- banking-style systems need traceability,
- audit history makes the workflow explainable,
- debugging is easier,
- the UI can show a step-by-step history.

## 9. Configurable Storage Backend

The project supports both memory and PostgreSQL workflow storage.

```text
WORKFLOW_STORAGE_BACKEND=memory
WORKFLOW_STORAGE_BACKEND=postgres
```

Reason:

- memory mode keeps local development simple,
- memory mode keeps standard tests fast,
- PostgreSQL mode demonstrates durable workflow persistence,
- both modes share the same API behaviour,
- deployment can use a managed PostgreSQL database without changing the application interface.

## 10. PostgreSQL for Durable Workflow Persistence

PostgreSQL was added to persist workflows and audit events beyond app/container restarts.

Reason:

- workflows are stateful by nature,
- audit events should survive restarts,
- relational constraints are useful for controlled state machines,
- PostgreSQL is widely used in production backends,
- the design prepares the app for managed database deployment.

The implementation uses:

```text
DatabaseWorkflowService
WorkflowRepository
SQLAlchemy models
psycopg
Alembic migrations
PostgreSQL JSONB metadata
CHECK constraints aligned with app Literals
```

## 11. Repository Layer for Database Access

Database access is isolated in `WorkflowRepository` rather than being placed directly in API routes or agent logic.

Reason:

- cleaner separation of concerns,
- easier testing,
- easier conversion between domain models and database records,
- service layer can control transactions,
- future storage changes are easier to manage.

## 12. Alembic Migrations

Alembic is used to version database schema changes.

Reason:

- schema changes should be explicit,
- local and cloud databases can be migrated consistently,
- the app does not silently create production tables at startup,
- migration execution can be separated from normal app runtime.

## 13. Masked Workflow Persistence

The PostgreSQL backend stores masked `user_request` text instead of raw sensitive user input.

Reason:

- support requests can contain identifiers,
- persistence increases the risk of accidental exposure,
- stored records should avoid unnecessary sensitive details,
- response and UI output should also avoid echoing raw identifiers.

This is a lightweight control for the project, not a complete enterprise PII solution.

## 14. Optional Gemini Response Generation

Gemini writes the final response from tool results when `use_llm=true`.

Reason:

- improves response wording,
- keeps deterministic tool execution,
- avoids model-controlled actions,
- keeps the system usable without LLM calls.

When `use_llm=false`, the system returns deterministic responses based on tool outputs.

## 15. Prompt Safety Checks

The project includes lightweight prompt safety checks for attempts to:

- ignore instructions,
- bypass confirmation,
- avoid audit logging,
- reveal system prompts or hidden instructions.

Reason:

- prompt injection is a practical risk in tool-using systems,
- unsafe requests should not trigger tools,
- the UI should make safety decisions visible.

## 16. FastAPI Backend

FastAPI exposes the agent and workflow system through HTTP.

Reason:

- typed request/response schemas,
- clear API contracts,
- automatic Swagger/OpenAPI docs,
- easy local and Docker deployment,
- good fit for Python AI services.

## 17. Lightweight Server-Rendered UI

The project uses a lightweight UI served by FastAPI with Jinja2, HTML, CSS, and JavaScript.

Reason:

- keeps the project focused on AI workflow engineering,
- avoids unnecessary frontend build complexity,
- provides a clear browser demo,
- supports workflow and audit-event inspection.

## 18. Docker and Docker Compose

Docker packages the FastAPI app consistently. Docker Compose runs the app with local PostgreSQL.

Reason:

- repeatable local runtime,
- simple database-backed development,
- easier cloud deployment path,
- clear separation between app and database containers.

## 19. Runtime Secrets Instead of Hard-Coded Keys

API keys and database connection strings are configured through environment variables.

Reason:

- secrets should not be committed,
- Docker images should not contain secrets,
- cloud deployments can inject secrets securely,
- local `.env` files stay private.

## 20. CI with Docker Smoke Testing

GitHub Actions runs Python tests and Docker smoke tests.

Reason:

- catches Python regressions,
- verifies the Docker image builds,
- confirms `/health` and `/ui` work from the container,
- improves confidence before deployment.

## 21. Known Project Boundaries

The project intentionally uses:

- mock banking tools,
- sample transaction data,
- lightweight prompt safety checks,
- lightweight UI,
- project-level masking rather than enterprise PII tooling.

These choices keep the project focused while still demonstrating controlled AI workflow design, durable persistence, testability, and cloud/container readiness.
