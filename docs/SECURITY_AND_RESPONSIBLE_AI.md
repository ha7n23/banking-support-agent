# Security and Responsible AI

## 1. Project Scope

The Banking Support Agent is a controlled AI workflow automation project built around a mock banking support use case.

The project demonstrates how a safer AI support assistant can:

- classify support requests,
- call restricted mock tools,
- check transaction and policy context,
- assess dispute eligibility,
- create mock dispute tickets only after confirmation,
- track workflow state,
- expose audit events,
- persist workflow data in PostgreSQL when configured,
- apply lightweight prompt safety checks,
- mask sensitive identifiers in API/UI output and stored workflow requests,
- provide a FastAPI API and lightweight web UI,
- run through Docker, Docker Compose, and CI.

This project does **not** connect to real banking systems, real customer accounts, real dispute operations, or live financial infrastructure. It uses mock data and mock tools to demonstrate AI engineering patterns safely.

The system should not be treated as a production banking assistant, compliance tool, fraud decisioning system, or final dispute authority.

---

## 2. Threat Model

The project treats the LLM as useful but untrusted.

Main risks considered:

### Prompt Injection

A user may try to override the application’s intended behaviour by asking the system to:

- ignore previous instructions,
- bypass confirmation,
- hide or avoid audit logging,
- reveal hidden system instructions.

### Unsafe Tool Execution

A tool-using agent can do more than generate text. It may retrieve information or change state.

In this project, creating a dispute ticket is treated as a state-changing action. It must not be executed directly from user text or model output.

### Excessive Agency

The project avoids giving the LLM broad autonomy. The model can help write a final response, but routing, tools, confirmation, workflow state, action execution, and persistence are controlled by Python.

### Sensitive Data Exposure

Banking support requests can contain sensitive identifiers such as CNICs, card numbers, account numbers, passwords, or API keys.

The project uses mock data, but it still applies lightweight masking to reduce accidental exposure in responses, UI output, and stored workflow requests.

### Hallucinated or Overconfident Claims

The assistant should not claim that a refund has been approved, a transaction has been reversed, or a dispute has been completed unless that outcome is returned by a verified tool or workflow state.

The project distinguishes between:

```text
a case being eligible for support
        vs
an actual dispute ticket being created
        vs
a final banking outcome being approved
```

### Missing Auditability

A workflow system that performs actions without traceability is unsafe. This project records workflow events such as creation, classification, tool calls, confirmation requirement, user confirmation, action completion, rejection, and failure.

---

## 3. Implemented Safety Controls

### 3.1 Restricted Tool Use

The project uses a small set of predefined mock tools. The agent does not have access to arbitrary APIs, arbitrary code execution, external banking systems, or unrestricted database operations.

Tool categories:

```text
Read-only tools       → retrieve facts
Decision-support      → assess eligibility or policy context
Action tools          → create mock tickets only after confirmation
```

### 3.2 Python-Controlled Orchestration

The LLM does not call tools directly.

Python controls:

- issue routing,
- transaction ID extraction,
- tool selection,
- tool execution,
- confirmation checks,
- workflow creation,
- workflow state transitions,
- dispute ticket action execution,
- database persistence.

### 3.3 Confirmation-Gated Actions

Creating a mock dispute ticket requires confirmation.

Without confirmation, the system can:

```text
check transaction status
retrieve policy context
check eligibility
create an awaiting_confirmation workflow
return a workflow ID
```

It cannot create the dispute ticket until the action is confirmed or the workflow is executed through the controlled endpoint.

### 3.4 Workflow State Machine

Workflow statuses are limited to known states:

```text
created
awaiting_confirmation
approved
completed
rejected
failed
```

Invalid transitions are blocked.

### 3.5 Audit Event Tracking

The system records events such as:

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

These events make workflow behaviour easier to inspect and explain.

### 3.6 PostgreSQL Integrity Controls

When PostgreSQL is enabled, workflow data is persisted in two tables:

```text
workflows
workflow_events
```

The schema includes:

- primary keys,
- a foreign key from events to workflows,
- `CHECK` constraints for issue types,
- `CHECK` constraints for workflow statuses,
- `CHECK` constraints for event types,
- indexed workflow/status fields,
- `JSONB` metadata for event details.

The database supports durability and integrity, while the application remains responsible for safety logic.

### 3.7 Sensitive Data Masking

The project masks sensitive-looking values in API/UI responses and persisted workflow requests.

Examples include:

```text
CNIC-like values
long card/account-like numbers
password-like strings
API-key-like strings
```

This reduces accidental exposure. It should not be treated as full enterprise PII detection.

### 3.8 Prompt Safety Checks

The project includes lightweight checks for unsafe instruction patterns.

Examples:

```text
ignore previous instructions
bypass confirmation
create a ticket without approval
hide audit logs
reveal system prompt
```

Unsafe requests can be blocked before tools run.

### 3.9 Runtime Secret Configuration

Secrets are configured outside the codebase.

Local development uses `.env` files that should not be committed.

Cloud deployment can inject secrets such as:

```text
GEMINI_API_KEY
DATABASE_URL
```

through a secrets manager or runtime environment configuration.

---

## 4. Responsible AI Principles Applied

### Tool-Result Grounding

Final answers should be based on completed tool results and workflow state.

The assistant should not invent:

- refund approvals,
- successful reversals,
- completed tickets,
- final dispute outcomes.

### Human/User Confirmation

Sensitive actions require confirmation before execution.

This keeps action execution separate from natural-language intent detection.

### Least Agency

The LLM has a narrow role:

```text
write a final response from known facts
```

It does not control the workflow.

### Transparency

The API response includes:

```text
tool_calls
requires_confirmation
workflow_id
workflow_status
risk_level
security_flags
```

The UI makes this information visible during demos.

### Data Minimisation

Stored workflow requests are masked to reduce unnecessary sensitive-data persistence.

---

## 5. Testing and Validation

Tests cover:

- routing behaviour,
- tool outputs,
- confirmation-gated action behaviour,
- workflow transitions,
- audit event creation,
- prompt safety checks,
- sensitive-data masking,
- API response schemas,
- database-backed workflow persistence through opt-in integration tests.

Tests avoid live Gemini calls by using deterministic behaviour and fake clients where needed.

Database integration tests are opt-in because they require PostgreSQL.

---

## 6. Security Boundaries

This project does not include:

- production authentication,
- role-based access control,
- real customer identity checks,
- real account ownership validation,
- live banking system integrations,
- production fraud or compliance logic,
- enterprise PII detection,
- production-grade monitoring and alerting.

These are intentional boundaries for a mock AI engineering project.

---

## 7. Production Considerations

A production banking deployment would require:

- approved authentication and authorization,
- customer/account ownership validation,
- integration with approved internal systems,
- strong secrets and key management,
- database backup and recovery processes,
- production audit logging and retention,
- formal PII governance,
- regulatory and compliance review,
- model risk management,
- monitoring, alerting, and incident response,
- human escalation and review workflows.

---

## 8. Summary

The Banking Support Agent demonstrates a controlled approach to AI workflow automation.

Key responsible AI design principle:

```text
The model can help communicate.
The application controls actions.
The workflow records decisions.
The database can persist state and audit history.
```

This makes the project a practical demonstration of safer LLM application engineering for banking-style support workflows while remaining clear about the limits of a mock implementation.
