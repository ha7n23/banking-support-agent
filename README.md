# Banking Support Agent

![CI](https://github.com/ha7n23/banking-support-agent/actions/workflows/ci.yml/badge.svg)

A controlled tool-using banking support agent built with Python, FastAPI, typed mock tools, optional Gemini response generation, confirmation-gated actions, Docker, and GitHub Actions CI.

This project demonstrates how an AI agent can support banking and fintech customer service workflows while keeping tool execution safe, testable, and controlled.

## Project Summary

The agent can handle support requests such as:

- QR payment disputes
- duplicate card charge issues
- mobile banking password recovery
- refund timeline questions
- dispute ticket action requests

The core idea is:

```text
Python controls routing and tool execution.
Tools provide structured facts and actions.
Gemini optionally writes the final customer-facing response.
Action tools require explicit confirmation.
```

This is intentionally safer than a fully autonomous agent because banking workflows require predictable behaviour, validation, and confirmation before actions are performed.

## Why This Project Matters

Many agent demos allow the LLM to decide everything. That can be risky in domains like banking.

This project demonstrates a safer pattern:

```text
Read-only tools can run automatically.
Decision-support tools can run automatically.
Action tools require confirmation.
```

For example, the agent can automatically check a transaction status or dispute eligibility, but it cannot create a dispute ticket unless `confirm_action=true`.

## Key Features

- Deterministic issue routing
- Transaction ID extraction
- Mock transaction status tool
- Mock policy context tool
- Mock dispute eligibility tool
- Confirmation-gated mock dispute ticket action
- Optional Gemini-generated final responses
- Deterministic fallback mode without LLM
- FastAPI backend
- Docker support
- GitHub Actions CI
- Unit and API tests
- Portfolio documentation

## Architecture

```text
User Request
↓
Deterministic Router
↓
Safe Tool Execution
↓
Optional Gemini Response Writer
↓
Final Agent Response
```

The LLM does not control tools directly. It only writes the final response from completed tool results when LLM-assisted mode is enabled.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Examples](docs/API_EXAMPLES.md)
- [Safety Model](docs/SAFETY_MODEL.md)
- [Design Decisions](docs/DESIGN_DECISIONS.md)

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic
- Google Gemini
- Pytest
- Docker
- GitHub Actions

## Project Structure

```text
banking-support-agent/
  docs/
    ARCHITECTURE.md
    API_EXAMPLES.md
    SAFETY_MODEL.md
    DESIGN_DECISIONS.md

  src/
    banking_agent/
      api/
        app.py
        dependencies.py
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

      tools/
        action_tools.py
        dispute_tools.py
        policy_tools.py
        transaction_tools.py

      runners/
        run_agent.py

  tests/
  Dockerfile
  requirements.txt
  pytest.ini
  pyrightconfig.json
  .env.example
  .dockerignore
  .gitignore
  README.md
```

## Tool Safety Model

The project separates tools into three categories.

### Read-Only Tools

These can run automatically because they only retrieve information:

```text
check_transaction_status
retrieve_policy_context
```

### Decision-Support Tools

These can run automatically because they apply rules but do not change system state:

```text
check_dispute_eligibility
```

### Action Tools

These require explicit confirmation:

```text
create_dispute_ticket
```

A dispute ticket is only created when:

```text
user requested a dispute action
transaction was checked
eligibility was checked
case is eligible
confirm_action is true
```

## Example Agent Flow

User request:

```text
Please raise a dispute for TX1001.
```

Without confirmation:

```text
1. Extract transaction ID: TX1001
2. Check transaction status
3. Retrieve QR dispute policy
4. Check dispute eligibility
5. Ask for confirmation
6. Do not create a ticket
```

With confirmation:

```text
1. Extract transaction ID: TX1001
2. Check transaction status
3. Retrieve QR dispute policy
4. Check dispute eligibility
5. Create mock dispute ticket
```

## Setup

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

## Run the Agent from CLI

Run the default QR dispute example:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py
```

Run a password reset example:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "I forgot my mobile banking password."
```

Run an action request without confirmation:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "Please raise a dispute for TX1001."
```

Expected behaviour:

```text
requires_confirmation = True
no dispute ticket is created
```

Run an action request with confirmation:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "Please raise a dispute for TX1001." --confirm-action
```

Expected behaviour:

```text
requires_confirmation = False
mock dispute ticket is created
ticket_id = DSP-TX1001
```

## Response Modes

The agent supports two response modes.

### Deterministic Mode

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py
```

In this mode, Python builds the final response directly from structured tool results.

### LLM-Assisted Mode

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --use-llm
```

In this mode, Python still controls routing and tool execution, but Gemini writes the final customer-facing response using only tool results.

The LLM is not allowed to create tickets or perform actions. Action tools are still controlled by Python and require confirmation.

## Run the API

Start the FastAPI server:

```bash
PYTHONPATH=src python -m uvicorn banking_agent.api.app:app --reload
```

Open the interactive API docs:

```text
http://127.0.0.1:8000/docs
```

Available endpoints:

```text
GET  /health
POST /support
```

## API Example

Request:

```json
{
  "user_request": "My QR payment TX1001 was deducted but the merchant did not receive it. What should I do?",
  "use_llm": false,
  "confirm_action": false
}
```

Expected behaviour:

```text
The agent checks the transaction, retrieves policy context, checks dispute eligibility, and returns guidance without creating a ticket.
```

Action request without confirmation:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "use_llm": false,
  "confirm_action": false
}
```

Expected behaviour:

```text
requires_confirmation: true
dispute_ticket: null
```

Action request with confirmation:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "use_llm": false,
  "confirm_action": true
}
```

Expected behaviour:

```text
requires_confirmation: false
dispute_ticket.ticket_id: DSP-TX1001
```

## Run Tests

Run the full test suite:

```bash
pytest
```

The tests cover:

- transaction tools
- policy tools
- dispute eligibility tools
- confirmation-gated action tools
- deterministic routing
- agent service behaviour
- prompt building
- LLM-assisted mode using fake generators
- FastAPI endpoints

Tests do not require live Gemini calls.

## Docker

Build the Docker image:

```bash
docker build -t banking-support-agent .
```

Run the API without LLM mode:

```bash
docker run --rm -p 8000:8000 banking-support-agent
```

Run with Gemini support:

```bash
docker run --rm --env-file .env -p 8000:8000 banking-support-agent
```

Open:

```text
http://127.0.0.1:8000/docs
```

The `.env` file is passed at runtime and is not copied into the Docker image.

## Continuous Integration

This project uses GitHub Actions.

On every push and pull request, CI:

- installs dependencies
- runs the pytest test suite
- builds the Docker image

Workflow file:

```text
.github/workflows/ci.yml
```

## Example Outputs

### QR Payment Dispute

Request:

```text
My QR payment TX1001 was deducted but the merchant did not receive it. What should I do?
```

Expected behaviour:

```text
Transaction TX1001 is checked.
QR payment dispute policy is retrieved.
Dispute eligibility is checked.
No ticket is created automatically.
```

### Dispute Action Without Confirmation

Request:

```text
Please raise a dispute for TX1001.
```

Expected behaviour:

```text
The agent investigates the case but asks for confirmation before creating a ticket.
```

### Dispute Action With Confirmation

Request:

```text
Please raise a dispute for TX1001.
```

With:

```text
confirm_action = true
```

Expected behaviour:

```text
A mock dispute ticket is created with ID DSP-TX1001.
```

## Current Status

Phase 7B complete:

- Controlled banking support agent implemented
- Typed mock tools added
- Deterministic issue router added
- Transaction ID extraction added
- Action request detection added
- Confirmation-gated action tool added
- Optional Gemini final response generation added
- FastAPI backend added
- Docker support added
- GitHub Actions CI added
- Architecture documentation added
- API examples added
- Safety model documented
- Design decisions documented
- Unit and API tests passing
- Docker image builds successfully in CI

## Future Improvements

Potential next improvements:

- add real RAG policy retrieval instead of mock policy context
- add more issue types
- add streaming LLM responses
- add authentication to the API
- add richer ticket workflow states
- add persistent ticket storage
- add LangGraph-style workflow orchestration
- add human approval UI for action confirmation
- add observability and structured logs