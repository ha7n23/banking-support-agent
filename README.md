# Banking Support Agent

![CI](https://github.com/ha7n23/banking-support-agent/actions/workflows/ci.yml/badge.svg)

A controlled banking support agent and workflow automation demo built with Python, FastAPI, typed mock tools, optional Gemini response generation, confirmation-gated actions, audit events, PostgreSQL workflow persistence, a lightweight browser UI, Docker, Docker Compose, and GitHub Actions CI.

This project demonstrates a safer way to build tool-using AI systems for banking and fintech workflows. The LLM does not freely execute tools. Python controls routing, tool execution, workflow state, confirmation gates, audit events, and persistence. Gemini can optionally be used only to write the final customer-facing response from completed tool results.

## Project Summary

The agent can handle support requests such as:

- QR payment disputes
- duplicate card charge issues
- mobile banking password recovery
- refund timeline questions
- dispute ticket action requests

The project includes a workflow automation layer. When a user requests an action, such as raising a dispute, the system can create a workflow, return a workflow ID, record audit events, wait for confirmation, execute the approved action, and mark the workflow as completed.

Workflow state can run in either:

```text
memory
postgres
```

The memory backend keeps the app simple for local development and fast tests. The PostgreSQL backend provides durable workflow persistence using SQLAlchemy, Alembic migrations, and Docker Compose.

Core idea:

```text
Python controls routing, tools, workflow state, approval gates, and persistence.
Tools provide structured facts and controlled actions.
Gemini optionally writes the final response from completed tool results.
Workflow events preserve an audit trail.
PostgreSQL can persist workflow state and audit history across app restarts.
```

## Why This Project Matters

Many AI agent demos allow the model to decide what to do and when to call tools. That is risky for banking-style workflows where actions should be predictable, auditable, and confirmation-gated.

This project demonstrates a safer pattern:

```text
Read-only tools can run automatically.
Decision-support tools can run automatically.
Action tools require explicit confirmation.
Workflow actions are tracked through state and audit events.
Workflow data can be persisted using PostgreSQL.
```

For example, the agent can automatically check a transaction status, retrieve policy context, and check dispute eligibility. It cannot create a dispute ticket unless the user confirms the action or the workflow is explicitly executed after approval.

## Key Features

- Deterministic issue routing
- Transaction ID extraction
- Typed mock banking tools
- Optional Gemini-generated final responses
- Deterministic fallback mode without LLM calls
- Confirmation-gated mock dispute ticket creation
- Workflow state tracking
- Configurable workflow storage backend: memory or PostgreSQL
- PostgreSQL-backed workflow persistence
- SQLAlchemy repository layer
- Alembic database migrations
- Workflow listing and inspection endpoints
- Workflow confirmation, rejection, execution, completion, and failure endpoints
- Audit event logging for workflow actions
- Masked workflow request persistence for safer handling of sensitive input
- Lightweight FastAPI browser UI at `/ui`
- FastAPI backend with typed request and response schemas
- Docker runtime using `requirements-docker.txt`
- Docker Compose setup for local PostgreSQL
- GitHub Actions CI with Python tests, Docker build cache, and Docker smoke tests
- Unit, API, and opt-in PostgreSQL integration tests
- Professional project documentation

## Architecture

```text
Browser UI / API Client
        ↓
FastAPI API Layer
        ↓
Support Agent Service
        ├── deterministic router
        ├── read-only tools
        ├── decision-support tools
        ├── confirmation-gated action tools
        └── optional Gemini response writer
        ↓
Workflow Automation Layer
        ├── workflow state
        ├── status transitions
        ├── action execution
        └── audit events
        ↓
Workflow Storage Backend
        ├── memory backend
        └── PostgreSQL backend
              ├── SQLAlchemy models
              ├── repository layer
              ├── Alembic migrations
              └── PostgreSQL tables
        ↓
Structured API Response
```

The LLM does not control tools directly. It only writes the final response from completed tool results when LLM-assisted mode is enabled.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Examples](docs/API_EXAMPLES.md)
- [Workflow Automation](docs/WORKFLOW_AUTOMATION.md)
- [Safety Model](docs/SAFETY_MODEL.md)
- [Design Decisions](docs/DESIGN_DECISIONS.md)
- [Security and Responsible AI](docs/SECURITY_AND_RESPONSIBLE_AI.md)
- [PostgreSQL Database](docs/DATABASE.md)
- [AWS Deployment](cloud_deployment_docs/aws/DEPLOYMENT.md)
- [AWS Deployment with RDS(PostgreSQL)](cloud_deployment_docs/aws/DEPLOYMENT_RDS.md)

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic
- Google Gemini
- Jinja2
- HTML/CSS/JavaScript
- PostgreSQL
- SQLAlchemy
- psycopg
- Alembic
- Pytest
- Docker
- Docker Compose
- GitHub Actions

## Project Structure

```text
banking-support-agent/
  alembic/
    env.py
    versions/
      001_create_workflow_tables.py

  docs/
    API_EXAMPLES.md
    ARCHITECTURE.md
    DATABASE.md
    DESIGN_DECISIONS.md
    SAFETY_MODEL.md
    SECURITY_AND_RESPONSIBLE_AI.md
    WORKFLOW_AUTOMATION.md

  src/
    banking_agent/
      api/
        app.py
        dependencies.py
        frontend_routes.py
        routes.py
        schemas.py

      core/
        config.py
        exceptions.py
        schemas.py

      database/
        connection.py
        models.py
        repositories.py

      generation/
        llm_client.py
        prompt_builder.py

      routing/
        router.py

      security/
        prompt_safety.py
        sensitive_data.py

      services/
        agent_service.py
        database_workflow_service.py
        workflow_service.py

      tools/
        action_tools.py
        dispute_tools.py
        policy_tools.py
        transaction_tools.py

      web/
        templates/
          index.html
        static/
          app.js
          styles.css

      runners/
        run_agent.py

  tests/
  alembic.ini
  docker-compose.yml
  Dockerfile
  requirements.txt
  requirements-docker.txt
  pytest.ini
  pyrightconfig.json
  .env.example
  .dockerignore
  .gitignore
  README.md
```

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file:

```env
APP_NAME=Banking Support Agent
ENVIRONMENT=development
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

WORKFLOW_STORAGE_BACKEND=memory
DATABASE_URL=postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent
```

The `.env` file is ignored by Git and should not be committed.

Start the API in memory mode:

```bash
PYTHONPATH=src python -m uvicorn banking_agent.api.app:app --reload
```

Open the browser UI:

```text
http://127.0.0.1:8000/ui
```

Swagger/OpenAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Run with Docker

Build the image:

```bash
DOCKER_BUILDKIT=1 docker build -t banking-support-agent .
```

Run the container:

```bash
docker run --rm --env-file .env -p 8000:8000 banking-support-agent
```

Open:

```text
http://127.0.0.1:8000/ui
```

For deterministic mode only, the app can also run without a Gemini key if `use_llm=false` is used in requests.

## Run with PostgreSQL using Docker Compose

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Run database migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Start the app with the PostgreSQL backend:

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

The Docker Compose setup runs:

```text
FastAPI app container
PostgreSQL database container
PostgreSQL Docker volume
```

The app container connects to PostgreSQL using the Compose service hostname:

```text
postgres
```

## Example Workflow Demo

Create a workflow through the support agent:

```bash
curl -X POST "http://127.0.0.1:8000/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Please raise a dispute for TX1001.",
    "use_llm": false,
    "confirm_action": false
  }'
```

Expected response includes:

```text
"requires_confirmation": true
"workflow_id": "WF-..."
"workflow_status": "awaiting_confirmation"
```

Inspect the workflow:

```bash
curl "http://127.0.0.1:8000/workflows/WF-YOURID"
```

Execute the approved workflow action:

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-YOURID/execute"
```

Expected result:

```text
workflow.status = completed
dispute_ticket_id = DSP-TX1001
```

## PostgreSQL Persistence Demo

When running with Docker Compose, create a workflow and list workflows:

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

If the workflow still appears after the app container restarts, the workflow is being persisted in PostgreSQL rather than only in application memory.

Inspect database rows directly:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "SELECT workflow_id, issue_type, status, created_at FROM workflows ORDER BY created_at DESC;"
```

Inspect audit events:

```bash
docker compose exec postgres psql -U banking_agent -d banking_agent -c "SELECT event_id, workflow_id, event_type, created_at FROM workflow_events ORDER BY created_at ASC;"
```

## Database Design

The PostgreSQL backend uses two main tables:

```text
workflows
workflow_events
```

The `workflows` table stores the current state of each support workflow.

The `workflow_events` table stores the audit trail for each workflow.

The relationship is:

```text
one workflow → many workflow events
```

The schema includes:

```text
primary keys
foreign key relationship
CHECK constraints aligned with app Literals
JSONB event metadata
indexes for common query patterns
timestamp fields
```

The backend stores masked user requests to reduce the risk of persisting sensitive identifiers entered by users.

More detail is available in [docs/DATABASE.md](docs/DATABASE.md).

## Testing

Run the standard test suite:

```bash
PYTHONPATH=src pytest -q
```

The standard test suite uses fast deterministic tests and skips database integration tests unless explicitly enabled.

The tests cover:

- routing behaviour
- tool behaviour
- agent service behaviour
- prompt building
- prompt safety checks
- sensitive-data masking
- confirmation-gated actions
- workflow state transitions
- workflow audit events
- workflow API endpoints
- frontend route loading
- FastAPI response schemas
- database-backed workflow service behaviour through opt-in integration tests

Tests do not call Gemini. Fake clients and deterministic responses are used where needed.

### PostgreSQL Integration Tests

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

## CI/CD

GitHub Actions runs:

```text
1. Python unit and API tests
2. Docker image build using GitHub Actions cache
3. Docker container smoke test
4. /health endpoint check
5. /ui route check
```

The Docker image uses a smaller runtime-specific `requirements-docker.txt` file to avoid installing unnecessary development dependencies in the container.

## Security and Responsible AI

This project includes safety-oriented design choices for banking-style AI workflows:

```text
deterministic routing
typed tool outputs
confirmation-gated actions
tool-result grounding
audit event tracking
sensitive-data masking
runtime secret configuration
database CHECK constraints
controlled workflow state transitions
```

The LLM is not allowed to independently execute tools or perform actions. Python controls routing, tool selection, workflow state, confirmation requirements, and action execution.

Sensitive values should not be committed to the repository. Use `.env.example` for placeholders and `.env` for local private values.

More detail is available in [docs/SECURITY_AND_RESPONSIBLE_AI.md](docs/SECURITY_AND_RESPONSIBLE_AI.md).

## Portfolio Summary

This project shows how to design a controlled AI workflow system rather than an uncontrolled chatbot. It demonstrates:

- safe tool use
- deterministic routing
- human/user confirmation gates
- workflow state management
- durable PostgreSQL workflow persistence
- audit event tracking
- SQLAlchemy repository design
- Alembic database migrations
- FastAPI API design
- browser-based demo UI
- Docker and Docker Compose packaging
- CI/CD validation
- integration testing for database-backed workflows

## Limitations and Future Improvements

This project uses mock banking tools and sample workflow data for demonstration. It is designed to show AI application engineering, controlled tool use, workflow automation, database persistence, and cloud/container readiness.

In a production banking environment, the system would require:

- real authentication and role-based access control
- integration with approved banking systems, CRM, case-management, or core banking platforms
- stronger permission checks before action execution
- production-grade audit logging and retention policies
- monitoring, alerting, and incident response
- human handoff and escalation workflows
- encryption and stricter secrets management
- formal data-governance and PII handling controls
- regulatory and compliance review
- production deployment infrastructure and environment separation

Future improvements could include:

- AWS RDS PostgreSQL deployment
- role-based workflow approval
- richer workflow dashboard
- stronger policy checks before action execution
- conversation history
- production monitoring and alerting
- infrastructure as code
- full cloud deployment with managed database persistence