# Banking Support Agent

A controlled tool-using banking support agent built with Python.

The project demonstrates how an AI agent can use typed tools, mock transaction data, policy context, and dispute eligibility checks to support banking/fintech customer service scenarios.

## Goal

This project focuses on the foundations of AI agents:

- tool design
- typed tool inputs and outputs
- read-only vs action tool separation
- deterministic routing
- safe banking support workflows
- tests for tool behaviour

## Run the Agent

Run the default QR dispute example:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py
```

Run a password reset example:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "I forgot my mobile banking password."
```

Run an action request example:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "Please raise a dispute for TX1001."
```

Action requests require confirmation before any ticket would be created.

## Response Modes

The agent supports two response modes.

### Deterministic Mode

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py
```

### LLM-Assisted Mode

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --use-llm
```

## Confirmation-Gated Actions

The agent separates read-only tools from action tools.

Read-only and decision-support tools can run automatically:

- check transaction status
- retrieve policy context
- check dispute eligibility

Action tools require explicit confirmation:

- create dispute ticket

Example without confirmation:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "Please raise a dispute for TX1001."
```

The agent checks the transaction and eligibility but does not create a ticket.

Example with confirmation:

```bash
PYTHONPATH=src python src/banking_agent/runners/run_agent.py --request "Please raise a dispute for TX1001." --confirm-action
```

## Run the API

Start the FastAPI server:

```bash
PYTHONPATH=src uvicorn banking_agent.api.app:app --reload
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

Example support request:

```json
{
  "user_request": "My QR payment TX1001 was deducted but the merchant did not receive it. What should I do?",
  "use_llm": false,
  "confirm_action": false
}
```

Example action request without confirmation:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "use_llm": false,
  "confirm_action": false
}
```

The agent investigates the case but does not create a ticket.

Example action request with confirmation:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "use_llm": false,
  "confirm_action": true
}
```

The agent creates a mock dispute ticket only after confirmation.

## Docker

Build the Docker image:

```bash
docker build -t banking-support-agent .
```

Run the API without LLM mode:

```bash
docker run --rm -p 8000:8000 banking-support-agent
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Run with Gemini support:

```bash
docker run --rm --env-file .env -p 8000:8000 banking-support-agent
```

The `.env` file is passed at runtime and is not copied into the Docker image.

The Docker container exposes:

```text
GET  /health
POST /support
```

## Current Status

Phase 6A complete:

- project structure created
- typed schemas added
- custom exceptions added
- mock transaction status tool added
- mock policy context tool added
- mock dispute eligibility tool added
- deterministic issue router added
- transaction ID extraction added
- action request detection added
- controlled agent service added
- agent runner added
- LLM-assisted final response generation added
- Gemini text generator added
- safe agent response prompt added
- deterministic and LLM response modes supported
- confirmation-gated mock dispute ticket action added
- action tool only runs after explicit confirmation
- FastAPI backend added
- `/health` and `/support` endpoints added
- Docker support added
- API can run in deterministic mode or LLM-assisted mode inside Docker
- unit tests added for tools, routing, agent behaviour, prompt building, action gating, and API behaviour

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate