# Safety Model

## Overview

This project is designed around a controlled agent safety model.

The agent does not freely decide and execute arbitrary actions. Python controls routing, tool execution, confirmation gates, workflow state, and audit events.

The LLM is optional and is used only as a final response writer.

## Core Principle

```text
Read-only tools can run automatically.
Decision-support tools can run automatically.
Action tools require explicit confirmation.
Workflow actions are tracked and audited.
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

Action tools change state or trigger workflows.

Example:

```text
create_dispute_ticket
```

These require explicit confirmation.

## Confirmation-Gated Action Flow

For a dispute ticket to be created, the controlled workflow must establish that:

```text
the user requested a dispute action
the transaction was checked
policy context was retrieved
eligibility was checked
the case is eligible
the action was confirmed
```

Without confirmation, the agent may investigate and explain, but it will not create a ticket.

## Workflow Safety

Action-oriented support requests can create a workflow.

A workflow records:

```text
workflow ID
issue type
transaction ID
status
recommended action
confirmation requirement
dispute ticket ID if completed
failure reason if failed
```

This prevents action execution from being hidden inside a single chatbot response.

## Safe Workflow Transitions

Workflow status changes go through controlled service methods.

Examples:

```text
awaiting_confirmation → approved
awaiting_confirmation → rejected
approved → completed
awaiting_confirmation → execute → completed
```

Invalid transitions raise controlled errors.

This protects against cases such as:

```text
executing a rejected workflow
confirming a workflow that is not awaiting confirmation
completing a workflow before approval
failing a completed workflow
```

## Audit Events

Every important workflow step creates an audit event.

Examples:

```text
workflow_created
confirmation_required
intent_classified
tool_called
user_confirmed
action_completed
action_rejected
workflow_failed
```

This supports traceability and debugging.

In production, these events would be persisted in a database or audit log service.

## Why This Matters

In banking and fintech, unsafe action execution can cause serious issues.

Examples of risky actions:

```text
creating a support ticket without consent
blocking a card
sending a message
changing account information
initiating a refund
modifying customer records
```

This project demonstrates a safer pattern:

```text
investigate automatically
ask for confirmation before action
execute only after confirmation
record the workflow history
```

## LLM Safety Boundary

The LLM does not control tools.

The workflow is:

```text
Python router decides route
tools execute under Python control
workflow service tracks action state
tool results are collected
LLM writes final response only if enabled
```

The prompt tells the LLM to:

- use only tool results
- avoid inventing policy details
- avoid inventing transaction facts
- avoid claiming a ticket was created unless the action tool confirms it
- explain confirmation requirements when an action was requested but not confirmed

## Deterministic Mode

The project can run without an LLM.

In deterministic mode, Python builds the final response from tool results.

This is useful for:

- testing
- debugging
- CI
- safe fallback behaviour
- running without API keys

## LLM-Assisted Mode

In LLM-assisted mode, Gemini writes the final response.

The tool execution and workflow state remain controlled by Python.

This gives better language quality without giving the LLM full autonomy.

## Mock Data and No Real Actions

The project uses mock tools and mock transaction data.

This avoids:

- real customer data
- real banking APIs
- accidental real actions
- API costs during tests
- compliance risk from using private data

The architecture can later be adapted to real APIs by replacing mock tool implementations while keeping the same safety boundaries.

## Production Safeguards Needed Later

For a real banking environment, the system would need:

- authentication
- role-based access control
- customer identity verification
- permission checks before actions
- persistent audit logs
- monitoring and alerting
- PII masking
- rate limits
- human escalation workflows
- data retention controls
- production incident handling

The current project is a safe, mock implementation that demonstrates the architecture and safety pattern.
