# Safety Model

## Overview

This project is designed around a controlled agent safety model.

The agent does not freely decide and execute arbitrary actions. Instead, Python code controls routing, tool execution, and confirmation-gated actions.

The LLM is optional and is used only as a final response writer.

## Core Principle

```text
Read-only tools can run automatically.
Decision-support tools can run automatically.
Action tools require explicit confirmation.
```

## Tool Categories

### Read-Only Tools

Read-only tools fetch information but do not change system state.

Examples:

```text
check_transaction_status
retrieve_policy_context
```

These can run automatically.

### Decision-Support Tools

Decision-support tools apply rules or provide recommendations but do not perform external actions.

Example:

```text
check_dispute_eligibility
```

This can run automatically because it does not create or update anything.

### Action Tools

Action tools change system state or trigger workflows.

Example:

```text
create_dispute_ticket
```

These require explicit confirmation.

## Confirmation-Gated Action Flow

For a dispute ticket to be created, all of the following must be true:

```text
user requested a dispute action
transaction was checked
eligibility was checked
case is eligible
confirm_action is true
```

Without confirmation, the agent may investigate and explain, but it will not create a ticket.

## Why This Matters

In banking and fintech, unsafe action execution can cause serious issues.

Examples of risky actions:

```text
creating a support ticket without consent
blocking a card
sending a message
changing account information
initiating a refund
```

This project demonstrates the safer pattern:

```text
investigate automatically
ask for confirmation before action
execute only after confirmation
```

## LLM Safety Boundary

The LLM does not control tools.

The workflow is:

```text
Python router decides tool route
tools execute
tool results are collected
LLM writes final response only if enabled
```

The prompt tells the LLM:

- use only tool results
- do not invent policy details
- do not claim a ticket was created unless the action tool result confirms it
- explain confirmation requirements when action was requested but not confirmed

## Deterministic Mode

The project can run without an LLM.

In deterministic mode, Python builds the final response from tool results.

This is useful for:

- testing
- debugging
- safe fallback behaviour
- running without API keys

## LLM-Assisted Mode

In LLM-assisted mode, Gemini writes the final response.

The tool execution remains controlled by Python.

This gives better language quality without giving the LLM full autonomy.

## Mock Data

The project uses mock tools and mock transaction data.

This avoids:

- real customer data
- real banking APIs
- accidental real actions
- API costs during tests

The architecture can later be adapted to real APIs by replacing mock tool implementations while keeping the same interfaces.