# Workflow Automation

## Overview

The workflow automation layer turns the agent from a simple request-response assistant into a controlled support workflow backend.

Instead of only returning an answer, the system can create and manage workflows for action-oriented support requests.

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

- traceability,
- approval gates,
- controlled status transitions,
- audit events,
- safe failure behaviour,
- clear separation between investigation and action execution,
- persistence when durability is required.

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

### `created`

A workflow exists but does not currently need confirmation.

### `awaiting_confirmation`

The agent identified a sensitive action and is waiting for explicit approval.

### `approved`

The action has been approved but has not yet been completed.

### `completed`

The confirmed action was executed successfully.

### `rejected`

The action was rejected and cannot be executed.

### `failed`

The workflow encountered a controlled error.

## Workflow Events

Workflow events preserve an audit trail.

A workflow can record events such as:

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

Each event includes:

```text
event_id
workflow_id
event_type
message
metadata
created_at
```

## Action Request Without Confirmation

Request:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "use_llm": false,
  "confirm_action": false
}
```

Expected behaviour:

```text
Agent checks transaction and policy context.
Agent checks dispute eligibility.
Agent identifies that ticket creation is an action.
Workflow is created as awaiting_confirmation.
No dispute ticket is created yet.
```

Response includes:

```text
requires_confirmation = true
workflow_id = WF-...
workflow_status = awaiting_confirmation
dispute_ticket = null
```

## Confirmed Action Flow

The action can be completed through the workflow endpoint:

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-YOURID/execute"
```

Expected behaviour:

```text
Workflow state is validated.
The action is treated as confirmed.
The mock dispute ticket is created.
Workflow status becomes completed.
Audit events are recorded.
```

Expected result:

```text
workflow.status = completed
dispute_ticket_id = DSP-TX1001
```

## Manual Confirmation and Rejection

Confirm a workflow:

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-YOURID/confirm"
```

Reject a workflow:

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-YOURID/reject"
```

Rejected workflows cannot be executed.

## Workflow Storage Backends

The workflow layer supports two storage backends.

### Memory Backend

```env
WORKFLOW_STORAGE_BACKEND=memory
```

The memory backend stores workflow state inside the running Python process.

Use it for:

```text
fast local development
standard unit tests
simple demos without PostgreSQL
```

Data is lost when the process or container restarts.

### PostgreSQL Backend

```env
WORKFLOW_STORAGE_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://banking_agent:banking_agent_password@localhost:5432/banking_agent
```

The PostgreSQL backend stores workflows and audit events in database tables.

Use it for:

```text
durable workflow state
audit event persistence
container restart persistence
cloud-style deployment patterns
database integration tests
```

The backend uses:

```text
DatabaseWorkflowService
WorkflowRepository
SQLAlchemy
Alembic
PostgreSQL
```

## Persistence Behaviour

With PostgreSQL enabled:

```text
Create workflow
        ↓
Workflow row is inserted into workflows
        ↓
Audit events are inserted into workflow_events
        ↓
App container restarts
        ↓
Workflow can still be listed and inspected
```

This proves the state is stored in PostgreSQL rather than only in memory.

## API Endpoints

Workflow endpoints include:

```text
GET  /workflows
GET  /workflows/{workflow_id}
GET  /workflows/{workflow_id}/events
POST /workflows/{workflow_id}/confirm
POST /workflows/{workflow_id}/reject
POST /workflows/{workflow_id}/execute
```

## UI Support

The lightweight UI at `/ui` supports:

- submitting support requests,
- viewing workflow IDs,
- listing workflows,
- inspecting workflow state,
- viewing audit events,
- executing confirmation-gated actions,
- displaying security review metadata.

## Invalid Transitions

Invalid transitions raise a controlled workflow error and return a safe API response.

Examples:

```text
executing a rejected workflow
executing a completed workflow again
confirming a workflow in an invalid status
rejecting an already completed workflow
```

This keeps workflow behaviour predictable and testable.

## Safety Role of Workflows

Workflow automation is also a safety control.

It prevents the system from treating a model-written answer as an action. The application must explicitly move the workflow through valid states before an action tool runs.

The result is:

```text
separate investigation from action
require confirmation before state changes
record audit events
preserve state in PostgreSQL when configured
return clear workflow status to the API/UI
```
