# Architecture

## Overview

The Banking Support Agent is a controlled tool-using support agent with workflow automation and durable storage options for banking and fintech-style scenarios.

The project demonstrates how an AI application can combine:

- deterministic routing,
- typed mock tools,
- optional LLM-assisted response generation,
- confirmation-gated action tools,
- workflow state tracking,
- audit events,
- memory or PostgreSQL workflow storage.

The core design principle is:

```text
Python controls the workflow.
Tools provide facts and controlled actions.
The LLM only writes the final response when enabled.
Workflow state and audit events make actions traceable.
PostgreSQL can persist workflows beyond app restarts.
```

## High-Level System Flow

```text
User / Browser UI / API Client
        ↓
FastAPI API Layer
        ↓
Support Agent Service
        ↓
Deterministic Router
        ↓
Safe Tool Execution
        ↓
Optional Gemini Response Writer
        ↓
Workflow Automation Layer
        ↓
Workflow Storage Backend
        ├── In-memory service
        └── PostgreSQL database service
        ↓
Structured Agent + Workflow Response
```

## Main Runtime Flows

### 1. Information-Only Support Flow

```text
User asks a question
        ↓
Router classifies intent and extracts details
        ↓
Read-only and decision-support tools run
        ↓
Agent returns answer
        ↓
No workflow is created if no tracked action is required
```

Example:

```text
I forgot my mobile banking password.
```

### 2. Action Request Without Confirmation

```text
User asks to raise a dispute
        ↓
Router detects requested action
        ↓
Tools check transaction, policy, and eligibility
        ↓
Agent requires confirmation
        ↓
Workflow is created as awaiting_confirmation
        ↓
Audit events are recorded
        ↓
Response returns workflow_id
```

Example:

```text
Please raise a dispute for TX1001.
```

The system may investigate the request, but it does not create the mock dispute ticket until confirmation is provided or the workflow is later executed through the controlled workflow endpoint.

### 3. Confirmed Action Flow

```text
Workflow is awaiting_confirmation
        ↓
User confirms or workflow execute endpoint is called
        ↓
System validates current workflow state
        ↓
Action tool runs under application control
        ↓
Mock dispute ticket is created
        ↓
Workflow status becomes completed
        ↓
Audit event records action completion
```

### 4. Unsafe Prompt Flow

```text
User attempts prompt injection or confirmation bypass
        ↓
Prompt safety check detects risky text
        ↓
Request is blocked or marked high risk
        ↓
No tools run
        ↓
No workflow action is executed
```

## Component Architecture

```text
FastAPI
├── /health
├── /support
├── /workflows
├── /workflows/{workflow_id}
├── /workflows/{workflow_id}/events
├── /workflows/{workflow_id}/confirm
├── /workflows/{workflow_id}/reject
├── /workflows/{workflow_id}/execute
└── /ui

Application Services
├── SupportAgentService
├── InMemoryWorkflowService
└── DatabaseWorkflowService

Workflow Storage
├── Memory backend
└── PostgreSQL backend
    ├── SQLAlchemy models
    ├── WorkflowRepository
    ├── Alembic migrations
    └── PostgreSQL tables

Safety Layer
├── Prompt safety checks
├── Sensitive data masking
├── Confirmation gates
└── Controlled workflow transitions

Tools
├── check_transaction_status
├── retrieve_policy_context
├── check_dispute_eligibility
└── create_dispute_ticket

Optional Generation
└── Gemini final response writer
```

## API Layer

The FastAPI layer is responsible for:

- exposing HTTP endpoints,
- validating request bodies,
- returning typed response schemas,
- applying response masking,
- wiring services through dependencies,
- serving the lightweight browser UI.

The API layer does not contain the core routing or workflow business logic. That behaviour belongs in service classes so it can be tested independently.

## Support Agent Service

`SupportAgentService` orchestrates a single support request.

It handles:

- prompt safety checks,
- issue classification through deterministic routing,
- transaction ID extraction,
- tool execution,
- confirmation requirement detection,
- optional workflow creation,
- optional dispute ticket creation,
- optional Gemini final response generation.

The support agent service does not store workflows directly. It uses the configured workflow service through a shared protocol/interface.

## Deterministic Router

The router uses Python rules to identify:

- issue type,
- transaction ID,
- whether the user is requesting an action.

This design keeps high-risk decisions outside the LLM and makes behaviour easier to test.

Supported issue types include:

```text
qr_payment_dispute
duplicate_card_charge
password_reset
refund_timeline
general
```

## Tool Layer

Tools are typed and controlled. They return structured objects rather than free-form text.

Tool categories:

```text
Read-only tools       → retrieve facts
Decision tools        → assess eligibility or policy rules
Action tools          → create mock dispute tickets after confirmation
```

The LLM does not call tools directly. The application decides which tools run.

## Workflow Automation Layer

The workflow layer tracks action-oriented requests through controlled states:

```text
created
awaiting_confirmation
approved
completed
rejected
failed
```

The workflow model records:

```text
workflow_id
user_request
customer_id
issue_type
transaction_id
status
requires_confirmation
recommended_action
created_at
updated_at
failure_reason
dispute_ticket_id
```

Workflow events record the audit trail:

```text
event_id
workflow_id
event_type
message
metadata
created_at
```

## Storage Backends

### Memory Backend

The in-memory backend is used for simple local development, fast tests, and demos that do not need durability.

```env
WORKFLOW_STORAGE_BACKEND=memory
```

Data is stored inside the Python process and is lost when the app restarts.

### PostgreSQL Backend

The PostgreSQL backend stores workflows and workflow events in a relational database.

```env
WORKFLOW_STORAGE_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent
```

It uses:

- `DatabaseWorkflowService`,
- `WorkflowRepository`,
- SQLAlchemy ORM models,
- Alembic migrations,
- PostgreSQL `JSONB` event metadata,
- database-level `CHECK` constraints.

This backend allows workflow state and audit history to survive app/container restarts.

## Database Layer

The database package contains:

```text
connection.py      engine and session factory
models.py          SQLAlchemy workflow and event models
repositories.py    persistence and conversion logic
```

The repository layer isolates persistence logic from the agent and API layers. The service layer controls commits and rollbacks so a workflow update and its audit events can be handled consistently.

## Dependency Wiring

The API dependency layer chooses the workflow storage backend at runtime:

```text
WORKFLOW_STORAGE_BACKEND=memory
        ↓
shared InMemoryWorkflowService

WORKFLOW_STORAGE_BACKEND=postgres
        ↓
request-scoped SQLAlchemy session
        ↓
DatabaseWorkflowService
```

This keeps the API stable while allowing storage to change by configuration.

## Browser UI Layer

The lightweight UI at `/ui` supports:

- support request submission,
- optional LLM mode,
- confirmation-gated action testing,
- workflow list viewing,
- workflow detail inspection,
- audit-event display,
- visible security review metadata.

The UI is intentionally server-served with Jinja2, HTML, CSS, and JavaScript. This keeps the project focused on AI workflow engineering rather than frontend framework complexity.

## LLM Role

Gemini is optional. When enabled, it writes the final user-facing response using completed tool results.

It does not:

- classify the request,
- choose tools,
- execute tools,
- override workflow state,
- bypass confirmation,
- create tickets directly.

This separation keeps the model useful for natural-language response quality without giving it uncontrolled agency.

## Security and Safety Controls

Key controls include:

- deterministic routing,
- restricted tool set,
- typed tool outputs,
- confirmation-gated action tools,
- prompt safety detection,
- response masking,
- masked workflow persistence,
- audit event tracking,
- database constraints for workflow/event types,
- runtime secret configuration.

## Deployment Architecture

The application can run locally through Python, Docker, or Docker Compose. The PostgreSQL backend can run locally with Docker Compose or against managed PostgreSQL.

The documented AWS RDS deployment uses:

```text
Amazon ECR image
        ↓
ECS Fargate task/service
        ↓
Application Load Balancer
        ↓
FastAPI app
        ↓
Secrets Manager DATABASE_URL
        ↓
Private Amazon RDS PostgreSQL
```

Deployment evidence and setup details are kept in `cloud_deployment_docs/aws/`.

## Testing Architecture

Tests cover:

- deterministic routing,
- tool behaviour,
- support-agent orchestration,
- prompt safety,
- sensitive-data masking,
- workflow state transitions,
- API endpoints,
- frontend route loading,
- database workflow service behaviour.

Database integration tests are opt-in because they require PostgreSQL:

```bash
export RUN_DATABASE_TESTS=1
export DATABASE_URL="postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent"
PYTHONPATH=src pytest -q tests/test_database_workflow_service.py
```

## Design Trade-Offs

The project uses mock banking tools and sample data so the architecture can be demonstrated safely without real financial systems or customer records.

The implementation prioritises:

- predictable behaviour,
- clear auditability,
- testability,
- safe action execution,
- durable workflow persistence,
- cloud/container readiness.
