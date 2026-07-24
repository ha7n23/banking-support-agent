# Database-Backed Workflow Storage

This project supports durable workflow persistence using PostgreSQL. The application can run with either an in-memory workflow backend for lightweight development or a PostgreSQL-backed workflow backend for production-style persistence.

## Overview

The support-agent manages controlled banking support workflows, including:

```text
workflow creation
workflow status transitions
human-in-the-loop confirmation
audit events
dispute ticket references
timestamps
```

The original in-memory workflow service is still supported for fast local development and unit testing. PostgreSQL adds durable storage so workflows and audit events can survive application restarts.

## Storage Backends

The workflow storage backend is selected using:

```env
WORKFLOW_STORAGE_BACKEND=memory
```

or:

```env
WORKFLOW_STORAGE_BACKEND=postgres
```

### Memory Backend

The memory backend stores workflow data inside the running Python process.

```env
WORKFLOW_STORAGE_BACKEND=memory
```

This mode is useful for:

```text
fast local development
unit tests
simple demos
running the app without PostgreSQL
```

Data stored in this mode is not durable. If the application process restarts, workflow state is lost.

### PostgreSQL Backend

The PostgreSQL backend stores workflow data in a relational database.

```env
WORKFLOW_STORAGE_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://banking_agent:banking_agent_password@postgres:5432/banking_agent
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

In Docker Compose, the database hostname is `postgres` because containers communicate using service names.

When running database integration tests from the host machine, the database hostname is usually `localhost`.

## Architecture

The database-backed workflow architecture is:

```text
FastAPI routes
↓
Workflow service
↓
Workflow repository
↓
SQLAlchemy session
↓
psycopg driver
↓
PostgreSQL database
```

The service layer handles workflow rules and status transitions.

The repository layer handles database reads and writes.

Database transactions are controlled at the service layer so workflow state changes and audit event inserts can be committed together.

## Local Docker Compose Setup

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run database migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Start the application with the PostgreSQL backend:

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

## Proving Persistence

Create a workflow through the API:

```bash
curl -s -X POST http://127.0.0.1:8000/support \
  -H "Content-Type: application/json" \
  -d '{"user_request":"Please raise a dispute for TX1001.","use_llm":false,"confirm_action":false}'
```

List workflows:

```bash
curl -s http://127.0.0.1:8000/workflows
```

Restart the application container:

```bash
docker compose restart app
```

List workflows again:

```bash
curl -s http://127.0.0.1:8000/workflows
```

If the workflow is still returned after the application container restarts, workflow data is being persisted in PostgreSQL rather than only in application memory.

## Direct PostgreSQL Checks

Inspect workflow rows:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "SELECT workflow_id, issue_type, status, created_at FROM workflows ORDER BY created_at DESC;"
```

Inspect audit events:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "SELECT event_id, workflow_id, event_type, created_at FROM workflow_events ORDER BY created_at ASC;"
```

## Database Schema

The first database schema includes two core tables:

```text
workflows
workflow_events
```

### `workflows`

The `workflows` table stores the current state of each support workflow.

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
failure_reason
dispute_ticket_id
created_at
updated_at
```

The `workflow_id` column is the primary key.

The `user_request` column stores masked text rather than raw sensitive user input. This reduces the risk of persisting personally identifiable information or sensitive identifiers.

### `workflow_events`

The `workflow_events` table stores the audit trail for each workflow.

Key columns:

```text
event_id
workflow_id
event_type
message
metadata
created_at
```

The `event_id` column is the primary key.

The `workflow_id` column is a foreign key referencing `workflows.workflow_id`.

The `metadata` column uses PostgreSQL `JSONB` because audit event details can vary by event type.

## Relationship Between Tables

The relationship is:

```text
one workflow → many workflow events
```

A workflow can have multiple audit events, such as:

```text
workflow_created
confirmation_required
user_confirmed
action_completed
workflow_failed
```

The `workflow_events.workflow_id` foreign key ensures that audit events cannot exist without a valid parent workflow.

## Constraints

The database includes `CHECK` constraints aligned with the application's allowed literal values.

Protected fields include:

```text
workflow status
issue type
workflow event type
```

This prevents invalid database states such as:

```text
status = almost_done
issue_type = random_issue
event_type = unknown_event
```

The application validates data at the Python layer, while PostgreSQL enforces key integrity rules at the database layer.

## Indexes

The schema includes indexes for common workflow queries:

```text
workflow status
issue type
created_at
workflow event timeline by workflow_id and created_at
```

These indexes support operations such as:

```text
listing newest workflows
filtering by workflow status
filtering by issue type
retrieving a workflow audit timeline
```

Indexes are used selectively to support important read patterns without adding unnecessary write overhead.

## Migrations

Alembic manages database schema changes.

The first migration creates:

```text
workflows table
workflow_events table
foreign key relationship
CHECK constraints
indexes
```

Run migrations with:

```bash
docker compose run --rm app alembic upgrade head
```

If the local PostgreSQL volume is deleted, migrations must be run again before using the PostgreSQL backend.

## Transactions

Workflow state changes and audit event inserts are handled transactionally.

For example, completing a workflow requires:

```text
updating the workflow status
setting the dispute ticket ID when applicable
inserting an action_completed audit event
```

These operations should either succeed together or fail together. This prevents inconsistent workflow history, such as a completed workflow with no corresponding audit event.

## Running Tests

Run the standard test suite:

```bash
PYTHONPATH=src pytest -q
```

Database integration tests are opt-in because they require PostgreSQL.

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run migrations if required:

```bash
docker compose run --rm app alembic upgrade head
```

Run database integration tests from the host machine:

```bash
export RUN_DATABASE_TESTS=1
export DATABASE_URL="postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent"

PYTHONPATH=src pytest -q tests/test_database_workflow_service.py
```

Unset the environment variables after testing:

```bash
unset RUN_DATABASE_TESTS
unset DATABASE_URL
```

## Cleanup

Stop containers while keeping database data:

```bash
docker compose down
```

Stop containers and delete the local PostgreSQL volume:

```bash
docker compose down -v
```

Use `down -v` carefully because it deletes the local PostgreSQL data volume.

## Security and Privacy

The PostgreSQL backend stores masked user requests instead of raw sensitive user text.

Sensitive values and environment-specific credentials should not be committed to GitHub.

Use `.env.example` for placeholders and documentation.

Use `.env` for local private values.

The `.env` file should remain ignored by Git.

## Production Considerations

This local PostgreSQL setup is designed for development and portfolio demonstration.

A production deployment would require additional controls, such as:

```text
managed database hosting
private database networking
secure secret management
database backups
migration strategy
role-based access control
monitoring and alerting
log retention policies
PII handling policy
```

For AWS deployment, PostgreSQL would typically be hosted using Amazon RDS for PostgreSQL, with database credentials managed securely and database access restricted to the application layer.