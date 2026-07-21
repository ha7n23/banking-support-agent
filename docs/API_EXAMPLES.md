# API Examples

The Banking Support Agent API is built with FastAPI.

Start the server locally:

```bash
PYTHONPATH=src python -m uvicorn banking_agent.api.app:app --reload
```

Or run through Docker:

```bash
docker run --rm --env-file .env -p 8000:8000 banking-support-agent
```

Open the browser UI:

```text
http://127.0.0.1:8000/ui
```

Open the interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Health Check

### Request

```bash
curl http://127.0.0.1:8000/health
```

### Example Response

```json
{
  "status": "ok",
  "app_name": "Banking Support Agent",
  "environment": "development"
}
```

## Support Endpoint

The main agent endpoint is:

```text
POST /support
```

Request body:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "use_llm": false,
  "confirm_action": false
}
```

Fields:

```text
user_request     customer/support request text
use_llm          whether Gemini should write the final response
confirm_action   whether a sensitive action is already confirmed
```

## Example 1: QR Payment Dispute Guidance

### Request

```bash
curl -X POST "http://127.0.0.1:8000/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "My QR payment TX1001 was deducted but the merchant did not receive it. What should I do?",
    "use_llm": false,
    "confirm_action": false
  }'
```

### Expected Behaviour

The agent should:

- check transaction status
- retrieve QR dispute policy context
- check dispute eligibility
- explain the case without creating a ticket

Since the user asked for guidance rather than directly asking to create a ticket, a tracked workflow may not be required.

## Example 2: Action Request Without Confirmation

### Request

```bash
curl -X POST "http://127.0.0.1:8000/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Please raise a dispute for TX1001.",
    "use_llm": false,
    "confirm_action": false
  }'
```

### Expected Behaviour

The agent should investigate the case, require confirmation, create a workflow, and return the workflow ID.

Expected response shape:

```json
{
  "user_request": "Please raise a dispute for TX1001.",
  "answer": "Transaction TX1001 is marked as deducted... confirmation would be required before creating any ticket.",
  "tool_calls": [
    {
      "tool_name": "check_transaction_status",
      "input_summary": "transaction_id=TX1001",
      "output_summary": "status=deducted, settlement=not_settled"
    },
    {
      "tool_name": "retrieve_policy_context",
      "input_summary": "issue_type=qr_payment_dispute",
      "output_summary": "digital_payments_policy.md / QR Payment Disputes"
    },
    {
      "tool_name": "check_dispute_eligibility",
      "input_summary": "transaction_id=TX1001, issue_type=qr_payment_dispute",
      "output_summary": "eligible=True, human_review=True"
    }
  ],
  "requires_confirmation": true,
  "dispute_ticket": null,
  "workflow_id": "WF-EXAMPLE",
  "workflow_status": "awaiting_confirmation"
}
```

## Example 3: List Workflows

### Request

```bash
curl "http://127.0.0.1:8000/workflows"
```

### Expected Behaviour

Returns all workflows in newest-first order.

Example response shape:

```json
[
  {
    "workflow_id": "WF-EXAMPLE",
    "user_request": "Please raise a dispute for TX1001.",
    "customer_id": null,
    "issue_type": "qr_payment_dispute",
    "transaction_id": "TX1001",
    "status": "awaiting_confirmation",
    "requires_confirmation": true,
    "recommended_action": "create_dispute_ticket",
    "failure_reason": null,
    "dispute_ticket_id": null
  }
]
```

## Example 4: Inspect One Workflow

### Request

```bash
curl "http://127.0.0.1:8000/workflows/WF-EXAMPLE"
```

### Expected Behaviour

Returns the current state of the workflow.

Key fields:

```text
workflow_id
issue_type
transaction_id
status
requires_confirmation
recommended_action
dispute_ticket_id
```

## Example 5: View Audit Events

### Request

```bash
curl "http://127.0.0.1:8000/workflows/WF-EXAMPLE/events"
```

### Expected Behaviour

Returns audit events for the workflow.

Expected event types may include:

```text
workflow_created
confirmation_required
intent_classified
tool_called
```

After execution, additional events may include:

```text
user_confirmed
tool_called
action_completed
```

## Example 6: Execute Workflow Action

This is the main controlled automation step.

### Request

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-EXAMPLE/execute"
```

### Expected Behaviour

If the workflow is awaiting confirmation, the system confirms it, reruns the controlled action path, creates the mock dispute ticket, completes the workflow, and returns both the workflow and support response.

Example response shape:

```json
{
  "workflow": {
    "workflow_id": "WF-EXAMPLE",
    "issue_type": "qr_payment_dispute",
    "transaction_id": "TX1001",
    "status": "completed",
    "dispute_ticket_id": "DSP-TX1001"
  },
  "support_response": {
    "requires_confirmation": false,
    "dispute_ticket": {
      "ticket_id": "DSP-TX1001",
      "transaction_id": "TX1001",
      "issue_type": "qr_payment_dispute",
      "status": "created"
    },
    "workflow_id": "WF-EXAMPLE",
    "workflow_status": "completed"
  }
}
```

## Example 7: Action Request With Immediate Confirmation

### Request

```bash
curl -X POST "http://127.0.0.1:8000/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Please raise a dispute for TX1001.",
    "use_llm": false,
    "confirm_action": true
  }'
```

### Expected Behaviour

The agent should create a mock dispute ticket immediately and return a completed workflow.

Expected result:

```json
{
  "requires_confirmation": false,
  "dispute_ticket": {
    "ticket_id": "DSP-TX1001",
    "transaction_id": "TX1001",
    "issue_type": "qr_payment_dispute",
    "status": "created"
  },
  "workflow_status": "completed"
}
```

## Example 8: Confirm or Reject Manually

Confirm:

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-EXAMPLE/confirm"
```

Reject:

```bash
curl -X POST "http://127.0.0.1:8000/workflows/WF-EXAMPLE/reject"
```

Rejected workflows cannot be executed.

## Example 9: LLM-Assisted Mode

### Request

```bash
curl -X POST "http://127.0.0.1:8000/support" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Please raise a dispute for TX1001.",
    "use_llm": true,
    "confirm_action": false
  }'
```

### Expected Behaviour

The agent still controls routing, tools, and workflow state.

Gemini only writes the final response from tool results.

Expected result:

```text
requires_confirmation: true
dispute_ticket: null
workflow_status: awaiting_confirmation
```

The model should not claim that a ticket was created unless `confirm_action=true` or the workflow execution endpoint successfully creates a dispute ticket.
