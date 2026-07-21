# Workflow Automation

## Overview

The workflow automation layer turns the agent from a simple request-response system into a controlled support workflow backend.

Instead of only returning an answer, the system can create and manage support workflows for action-oriented requests.

Example:

```text
User: Please raise a dispute for TX1001.
        ↓
Agent investigates the case
        ↓
Workflow is created
        ↓
Workflow waits for confirmation
        ↓
Action is executed after approval
        ↓
Workflow is completed
        ↓
Audit events preserve the trace
```

## Why Workflow State Matters

Banking workflows need more than a chatbot response. They require:

- traceability
- approval gates
- controlled status transitions
- audit events
- safe failure behaviour
- clear separation between investigation and action execution

The workflow layer demonstrates these ideas in a simplified portfolio-friendly way.

## Workflow Model

A workflow tracks:

```text
workflow_id
user_request
customer_id
issue_type
transaction_id
status
requires_confirmation
recommended_action
created_at
updated_at
failure_reason
dispute_ticket_id
```

## Workflow Statuses

```text
created
awaiting_confirmation
approved
completed
rejected
failed
```

### created

A workflow exists but does not currently need confirmation.

### awaiting_confirmation

The agent identified a sensitive action and is waiting for explicit approval.

### approved

The action has been approved but has not yet been completed.

### completed

The action was executed successfully.

### rejected

The user or reviewer rejected the recommended action.

### failed

The workflow could not be completed due to an error or failed action result.

## Audit Events

Every important workflow step records an event.

Event types:

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

Audit events include:

```text
event_id
workflow_id
event_type
message
created_at
metadata
```

This makes the workflow traceable.

## Main Workflow Endpoints

```text
POST /workflows
GET  /workflows
GET  /workflows/{workflow_id}
GET  /workflows/{workflow_id}/events
POST /workflows/{workflow_id}/confirm
POST /workflows/{workflow_id}/reject
POST /workflows/{workflow_id}/complete
POST /workflows/{workflow_id}/fail
POST /workflows/{workflow_id}/execute
```

## Support Endpoint Integration

The `/support` endpoint creates a workflow automatically when the agent response needs workflow tracking.

A workflow is created when:

```text
the agent requires confirmation before an action
or
the agent created a dispute ticket after confirmation
```

The support response includes:

```text
workflow_id
workflow_status
```

This lets the caller continue the workflow through `/workflows/{workflow_id}/execute`, `/confirm`, or `/reject`.

## Workflow Execution Endpoint

The execution endpoint is:

```text
POST /workflows/{workflow_id}/execute
```

For this demo, the executable workflow action is:

```text
create_dispute_ticket
```

The endpoint:

```text
loads the workflow
checks the recommended action
confirms the workflow if it is awaiting confirmation
runs the agent action path with confirm_action=true
records tool calls
creates the mock dispute ticket
marks the workflow completed
returns workflow state and support response
```

## Safe Transition Examples

Allowed:

```text
awaiting_confirmation → approved
awaiting_confirmation → rejected
approved → completed
created → completed
awaiting_confirmation → execute → completed
```

Rejected:

```text
rejected → execute
completed → fail
created → confirm
awaiting_confirmation → complete directly
```

Invalid transitions raise a controlled `InvalidWorkflowTransitionError` and return a safe API error.

## In-Memory State

The workflow service uses in-memory storage:

```text
_workflows: dict[str, SupportWorkflow]
_events: dict[str, list[WorkflowEvent]]
```

This is intentional for the portfolio project because it keeps the project lightweight and deterministic.

In production, this would be replaced by persistent storage such as PostgreSQL, SQLite, DynamoDB, or a case-management platform.

## UI Support

The lightweight UI at `/ui` supports:

- submitting support requests
- viewing agent answers
- viewing tool calls
- viewing workflow status
- executing workflows
- refreshing workflow queue
- viewing audit events

This makes the workflow easier to demonstrate without relying only on Swagger or curl.
