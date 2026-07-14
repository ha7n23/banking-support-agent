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

## Current Status

Phase 3 complete:

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
- unit tests added for tools, routing, agent behaviour, and prompt building

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate