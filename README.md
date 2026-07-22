# Banking Support Agent

![CI](https://github.com/ha7n23/banking-support-agent/actions/workflows/ci.yml/badge.svg)

A controlled banking support agent and workflow automation demo built with Python, FastAPI, typed mock tools, optional Gemini response generation, confirmation-gated actions, audit events, a lightweight browser UI, Docker, and GitHub Actions CI.

This project demonstrates a safer way to build tool-using AI systems for banking and fintech workflows. The LLM does not freely execute tools. Python controls routing, tool execution, workflow state, confirmation gates, and audit events. Gemini can optionally be used only to write the final customer-facing response from completed tool results.

## Project Summary

The agent can handle support requests such as:

- QR payment disputes
- duplicate card charge issues
- mobile banking password recovery
- refund timeline questions
- dispute ticket action requests

The project now includes a workflow automation layer. When a user requests an action, such as raising a dispute, the system can create a workflow, return a workflow ID, record audit events, wait for confirmation, execute the approved action, and mark the workflow as completed.

Core idea:

```text
Python controls routing, tools, workflow state, and approval gates.
Tools provide structured facts and controlled actions.
Gemini optionally writes the final response from completed tool results.
Workflow events preserve an audit trail.
```

## Why This Project Matters

Many AI agent demos allow the model to decide what to do and when to call tools. That is risky for banking-style workflows where actions should be predictable, auditable, and confirmation-gated.

This project demonstrates a safer pattern:

```text
Read-only tools can run automatically.
Decision-support tools can run automatically.
Action tools require explicit confirmation.
Workflow actions are tracked through state and audit events.
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
- Workflow listing and inspection endpoints
- Workflow confirmation, rejection, execution, completion, and failure endpoints
- Audit event logging for workflow actions
- Lightweight FastAPI browser UI at `/ui`
- FastAPI backend with typed request and response schemas
- Docker-optimised runtime using `requirements-docker.txt`
- GitHub Actions CI with Python tests, Docker build cache, and Docker smoke tests
- Unit and API tests
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

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic
- Google Gemini
- Jinja2
- HTML/CSS/JavaScript
- Pytest
- Docker
- GitHub Actions

## Project Structure

```text
banking-support-agent/
  docs/
    API_EXAMPLES.md
    ARCHITECTURE.md
    DESIGN_DECISIONS.md
    SAFETY_MODEL.md
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

      generation/
        llm_client.py
        prompt_builder.py

      routing/
        router.py

      services/
        agent_service.py
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
```

The `.env` file is ignored by Git and should not be committed.

Start the API:

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

## Testing

Run all tests:

```bash
pytest
```

The tests cover:

- routing behaviour
- tool behaviour
- agent service behaviour
- prompt building
- confirmation-gated actions
- workflow state transitions
- workflow audit events
- workflow API endpoints
- frontend route loading
- FastAPI response schemas

Tests do not call Gemini. Fake clients and deterministic responses are used where needed.

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

## Portfolio Summary

This project shows how to design a controlled AI workflow system rather than an uncontrolled chatbot. It demonstrates:

- safe tool use
- deterministic routing
- human/user confirmation gates
- workflow state management
- audit event tracking
- FastAPI API design
- browser-based demo UI
- Docker packaging
- CI/CD validation

## Limitations and Future Improvements

This project uses mock banking tools and in-memory workflow state for demonstration.

In a production banking environment, the system would require:

- persistent database storage
- authentication and role-based access control
- audit-log persistence
- permission checks before actions
- monitoring and alerting
- human handoff workflows
- integration with real core banking, CRM, or case-management systems
- stricter data-governance and PII controls

Future improvements could include:

- persistent workflow storage with SQLite/PostgreSQL
- a richer workflow dashboard
- stronger policy checks before action execution
- role-based workflow approval
- conversation history
- deployment to a cloud container service
