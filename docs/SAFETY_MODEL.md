# Safety Model

## Overview

The Banking Support Agent is designed around a controlled agent safety model.

The agent does not freely decide or execute arbitrary actions. Python controls routing, tool execution, confirmation gates, workflow state, audit events, and persistence.

The LLM is optional and is used only as a final response writer after controlled tool execution.

## Core Principle

```text
Read-only tools can run automatically.
Decision-support tools can run automatically.
Action tools require explicit confirmation.
Workflow actions are tracked and audited.
Workflow state can be persisted in PostgreSQL.
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

Action tools change state or trigger a support action.

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
the action was confirmed
```

Without confirmation, the agent may investigate and explain, but it will not create a ticket.

## Workflow Safety

Action-oriented requests can create a workflow.

A workflow records:

```text
workflow_id
issue_type
transaction_id
status
requires_confirmation
recommended_action
dispute_ticket_id
timestamps
```

Workflow statuses are controlled:

```text
created
awaiting_confirmation
approved
completed
rejected
failed
```

Invalid transitions are rejected by application logic.

## Audit Events

The system records audit events for workflow activity.

Examples:

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

Audit events help explain what happened and why a workflow moved to a given state.

## PostgreSQL Persistence Safety

When `WORKFLOW_STORAGE_BACKEND=postgres`, workflows and events are stored in PostgreSQL.

Safety-relevant database controls include:

- masked `user_request` persistence,
- valid workflow status constraints,
- valid issue type constraints,
- valid event type constraints,
- foreign key relationship between workflows and events,
- durable audit history across app restarts.

The database does not replace application-level safety logic. It adds persistence and integrity checks behind the controlled workflow service.

## Sensitive Data Masking

The project includes lightweight masking for sensitive identifiers in API/UI output and stored workflow requests.

Examples of sensitive input patterns include:

```text
CNIC-like values
long card/account-like numbers
password-like strings
API-key-like strings
```

The goal is to reduce accidental exposure in responses, UI output, and persisted workflow records.

This is not a full enterprise PII detection system.

## Prompt Safety Checks

The project checks for unsafe prompt patterns such as:

- asking the system to ignore previous instructions,
- asking to bypass confirmation,
- asking to avoid audit logging,
- asking to reveal hidden system instructions.

Unsafe requests can be marked high risk and blocked before tool execution.

## LLM Boundary

Gemini may be used to write the final response.

Gemini does not:

- choose tools,
- execute tools,
- create dispute tickets,
- update workflow state,
- approve actions,
- bypass safety checks.

The response writer receives completed tool results and workflow state. It should not invent outcomes that tools did not return.

## Deterministic Mode

The app can run with:

```json
{
  "use_llm": false
}
```

This mode is useful for:

- tests,
- demos without API keys,
- reproducible behaviour,
- CI environments.

Tests use fake clients and deterministic responses rather than live Gemini calls.

## Not a Production Banking System

This project uses mock data and mock tools. It does not connect to real banking systems, real customer accounts, real dispute operations, or live financial infrastructure.

A production banking system would need:

- strong authentication and authorization,
- account ownership checks,
- production-grade audit logging,
- enterprise PII detection and retention controls,
- fraud/compliance review,
- human escalation workflows,
- monitoring and incident response,
- formal model and prompt governance.

## Summary

The safety model is based on separation of responsibilities:

```text
Python controls behaviour.
Tools return structured facts.
Actions require confirmation.
Workflows preserve state.
Events preserve audit history.
PostgreSQL can persist that history.
The LLM only writes grounded final responses.
```
