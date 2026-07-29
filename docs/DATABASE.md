# PostgreSQL Workflow Persistence

## Overview

The Banking Support Agent supports durable workflow persistence using PostgreSQL. The application can run with either an in-memory workflow backend for lightweight development or a PostgreSQL-backed backend for durable state and audit history.

The workflow layer manages:

```text
workflow creation
workflow status transitions
human/user confirmation gates
action execution
audit events
dispute ticket references
timestamps
```

The in-memory backend is still useful for fast development and unit tests. The PostgreSQL backend stores workflow records and audit events so they survive application and container restarts.

## Storage Backends

The backend is selected by environment variable:

```env
WORKFLOW_STORAGE_BACKEND=memory
```

or:

```env
WORKFLOW_STORAGE_BACKEND=postgres
```

### Memory Backend

```env
WORKFLOW_STORAGE_BACKEND=memory
```

Use this mode for:

```text
fast local development
unit tests
running without a database
simple deterministic demos
```

Data is stored inside the Python process. It is not durable.

### PostgreSQL Backend

```env
WORKFLOW_STORAGE_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent
```

Use this mode for:

```text
durable workflow state
audit event persistence
container restart persistence
database-backed integration tests
cloud-style deployment patterns
```

The PostgreSQL backend uses:

```text
DatabaseWorkflowService
WorkflowRepository
SQLAlchemy
psycopg
PostgreSQL
Alembic migrations
```

## Architecture

```text
FastAPI routes
        ↓
Workflow service protocol
        ↓
DatabaseWorkflowService
        ↓
WorkflowRepository
        ↓
SQLAlchemy session
        ↓
PostgreSQL database
        ↓
workflows + workflow_events tables
```

The API layer depends on a workflow service protocol rather than a concrete storage class. This lets the application switch between memory and PostgreSQL without changing endpoint behaviour.

## Database Package

```text
src/banking_agent/database/
  connection.py
  models.py
  repositories.py
```

### `connection.py`

Responsible for:

```text
creating the SQLAlchemy engine lazily
creating the session factory
providing database sessions
failing clearly when DATABASE_URL is missing in postgres mode
```

### `models.py`

Defines SQLAlchemy ORM models for:

```text
WorkflowRecord
WorkflowEventRecord
```

The models use PostgreSQL-specific types where useful, including `JSONB` for event metadata.

### `repositories.py`

Responsible for:

```text
saving workflow records
saving workflow event records
loading workflow state
loading workflow events
converting between Pydantic domain models and SQLAlchemy records
```

The repository uses `flush()` but does not control transaction commits. The service layer controls commit/rollback so workflow updates and related events stay consistent.

## Tables

### `workflows`

Stores the current state of each workflow.

Key columns:

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

Notes:

- `workflow_id` uses the app's readable `WF-...` identifier format.
- `user_request` stores masked text rather than raw sensitive input.
- `issue_type` and `status` are constrained to valid application values.
- `transaction_id` can store values such as `TX1001`.
- `dispute_ticket_id` can store values such as `DSP-TX1001` after completion.

### `workflow_events`

Stores the audit trail for workflow actions and transitions.

Key columns:

```text
event_id
workflow_id
event_type
message
metadata
created_at
```

Notes:

- `workflow_id` references `workflows.workflow_id`.
- `event_type` is constrained to valid application event types.
- `metadata` is stored as PostgreSQL `JSONB` because event details vary by event type.
- Event messages and metadata values are masked where appropriate.

## Relationship

```text
one workflow → many workflow events
```

A workflow can have events such as:

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

## Constraints and Integrity

The database schema includes:

```text
primary keys
foreign key relationship
CHECK constraints for issue_type
CHECK constraints for workflow status
CHECK constraints for event_type
indexes for workflow_id, status, issue_type, and created_at
```

The application validates data through Pydantic and Python domain models. PostgreSQL also enforces important integrity rules at the database layer.

This gives two layers of protection:

```text
Application layer validation
        +
Database layer constraints
```

## Alembic Migrations

Migration files are stored in:

```text
alembic/versions/
```

Current migration:

```text
001_create_workflow_tables.py
```

Run migrations locally:

```bash
docker compose run --rm app alembic upgrade head
```

Or from an environment with access to the configured database:

```bash
alembic upgrade head
```

The migration creates:

```text
workflows table
workflow_events table
foreign key relationship
CHECK constraints
indexes
JSONB metadata column
```

## Local Docker Compose Setup

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Start the app with PostgreSQL:

```bash
docker compose up --build app
```

The app is available at:

```text
http://127.0.0.1:8000
```

Useful checks:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/ui
curl -s http://127.0.0.1:8000/workflows
```

## Persistence Validation

Create a workflow:

```bash
curl -X POST "http://127.0.0.1:8000/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Please raise a dispute for TX1001.",
    "use_llm": false,
    "confirm_action": false
  }'
```

List workflows:

```bash
curl -s http://127.0.0.1:8000/workflows
```

Restart the app container:

```bash
docker compose restart app
```

List workflows again:

```bash
curl -s http://127.0.0.1:8000/workflows
```

If the same workflow remains visible after restart, state is being loaded from PostgreSQL.

## Direct PostgreSQL Checks

Inspect workflow rows:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "SELECT workflow_id, issue_type, status, created_at FROM workflows ORDER BY created_at DESC;"
```

Inspect audit events:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "SELECT event_id, workflow_id, event_type, created_at FROM workflow_events ORDER BY created_at ASC;"
```

Check table list:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "\dt"
```

## Database Integration Tests

Database integration tests are opt-in because they require PostgreSQL.

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Run integration tests:

```bash
export RUN_DATABASE_TESTS=1
export DATABASE_URL="postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent"

PYTHONPATH=src pytest -q tests/test_database_workflow_service.py
```

Unset the variables afterwards:

```bash
unset RUN_DATABASE_TESTS
unset DATABASE_URL
```

These tests validate:

```text
workflow persistence
workflow event persistence
status transitions
completed action flow
invalid transition behaviour
unknown workflow handling
```

## Masking and Sensitive Data Handling

The PostgreSQL backend stores masked user requests instead of raw sensitive text.

This matters because banking support requests may contain:

```text
card numbers
account numbers
CNICs
long numeric identifiers
password-like strings
API keys
```

The masking layer reduces accidental exposure in stored workflow records, API responses, and UI output. It is a lightweight project-level control, not a replacement for enterprise PII governance.

## Transaction Handling

The database workflow service controls transaction boundaries.

Typical pattern:

```text
load workflow
validate transition
update workflow
add event
commit
```

If an error occurs, the service rolls back the session so partial updates are not persisted.

## Local Cleanup

Stop containers:

```bash
docker compose down
```

Stop containers and delete the local PostgreSQL volume:

```bash
docker compose down -v
```

Use `down -v` carefully because it deletes local PostgreSQL data.

## Cloud Deployment Notes

The same PostgreSQL backend can run against managed PostgreSQL by setting `DATABASE_URL` to the managed database connection string and running Alembic migrations before the app uses the database.

The AWS RDS deployment documentation is kept separately in:

```text
cloud_deployment_docs/aws/DEPLOYMENT_RDS.md
```

That deployment uses Amazon RDS for PostgreSQL, ECS Fargate, ECR, Secrets Manager, CloudWatch, and an Application Load Balancer.

## Limitations

This database design is appropriate for a focused AI workflow engineering project. A production banking deployment would need additional controls such as:

- production authentication and authorization,
- tenant/account ownership checks,
- migration automation and rollback planning,
- stronger encryption and key management policies,
- production monitoring and alerting,
- audit log retention policies,
- formal PII classification and retention rules,
- backup and disaster recovery processes.
