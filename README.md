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

## Current Status

Phase 2 complete:

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
- unit tests added for tools, routing, and agent behaviour

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate