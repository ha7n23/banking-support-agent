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

## Support Request

The main endpoint is:

```text
POST /support
```

Request body:

```json
{
  "user_request": "My QR payment TX1001 was deducted but the merchant did not receive it. What should I do?",
  "use_llm": false,
  "confirm_action": false
}
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

### Example Response Shape

```json
{
  "user_request": "My QR payment TX1001 was deducted but the merchant did not receive it. What should I do?",
  "answer": "Transaction TX1001 is marked as deducted...",
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
  "requires_confirmation": false,
  "dispute_ticket": null
}
```

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

The agent should investigate the case but not create a ticket.

Expected result:

```text
requires_confirmation: true
dispute_ticket: null
```

## Example 3: Action Request With Confirmation

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

The agent should create a mock dispute ticket.

Expected result:

```json
{
  "requires_confirmation": false,
  "dispute_ticket": {
    "ticket_id": "DSP-TX1001",
    "transaction_id": "TX1001",
    "issue_type": "qr_payment_dispute",
    "status": "created"
  }
}
```

## Example 4: LLM-Assisted Mode

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

The agent still controls routing and tools.

Gemini only writes the final response from tool results.

Expected result:

```text
requires_confirmation: true
dispute_ticket: null
```

The model should not claim that a ticket was created unless `confirm_action` is true and the action tool returns a created ticket.