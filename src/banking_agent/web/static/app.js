const form = document.getElementById("support-form");
const userRequestInput = document.getElementById("user-request");
const useLlmInput = document.getElementById("use-llm");
const confirmActionInput = document.getElementById("confirm-action");
const submitButton = document.getElementById("submit-button");

const statusPill = document.getElementById("status-pill");
const errorBox = document.getElementById("error-box");
const answerText = document.getElementById("answer-text");
const securitySummary = document.getElementById("security-summary");
const workflowSummary = document.getElementById("workflow-summary");
const toolCallsList = document.getElementById("tool-calls-list");
const eventsList = document.getElementById("events-list");
const workflowsList = document.getElementById("workflows-list");

const executeWorkflowButton = document.getElementById("execute-workflow-button");
const refreshWorkflowsButton = document.getElementById("refresh-workflows-button");

let activeWorkflowId = null;

function setStatus(label, statusClass) {
  statusPill.textContent = label;
  statusPill.className = `status-pill ${statusClass}`;
}

function setError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}

function createTextElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = textContent;
  return element;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderSecuritySummary(data) {
  const riskLevel = data.risk_level || "low";
  const securityFlags = data.security_flags || [];

  const flagsText =
    securityFlags.length > 0 ? securityFlags.join(", ") : "None";

  securitySummary.className = "";
  securitySummary.innerHTML = `
    <div class="item-title">
      Risk level:
      <span class="status-tag ${escapeHtml(riskLevel)}">
        ${escapeHtml(riskLevel)}
      </span>
    </div>
    <div class="item-meta">
      Security flags: ${escapeHtml(flagsText)}
    </div>
  `;
}

function renderToolCalls(toolCalls) {
  toolCallsList.innerHTML = "";

  if (!toolCalls || toolCalls.length === 0) {
    toolCallsList.textContent = "No tool calls returned.";
    toolCallsList.className = "empty-state";
    return;
  }

  toolCallsList.className = "";

  toolCalls.forEach((toolCall) => {
    const item = document.createElement("div");
    item.className = "item";

    item.appendChild(
      createTextElement("div", "item-title", toolCall.tool_name)
    );
    item.appendChild(
      createTextElement("div", "item-meta", toolCall.input_summary)
    );
    item.appendChild(
      createTextElement("div", "item-text", toolCall.output_summary)
    );

    toolCallsList.appendChild(item);
  });
}

function renderWorkflowSummary(data) {
  activeWorkflowId = data.workflow_id;

  if (!data.workflow_id) {
    workflowSummary.textContent = "No workflow was created for this request.";
    workflowSummary.className = "empty-state";
    executeWorkflowButton.disabled = true;
    return;
  }

  workflowSummary.className = "";
  workflowSummary.innerHTML = `
    <div class="item-title">Workflow ${escapeHtml(data.workflow_id)}</div>
    <div class="item-meta">
      Status:
      <span class="status-tag ${escapeHtml(data.workflow_status)}">
        ${escapeHtml(data.workflow_status)}
      </span>
    </div>
    <div class="item-meta">
      Requires confirmation: ${String(data.requires_confirmation)}
    </div>
  `;

  executeWorkflowButton.disabled = data.workflow_status !== "awaiting_confirmation";
}

function renderEvents(events) {
  eventsList.innerHTML = "";

  if (!events || events.length === 0) {
    eventsList.textContent = "No audit events returned.";
    eventsList.className = "empty-state";
    return;
  }

  eventsList.className = "";

  events.forEach((event) => {
    const item = document.createElement("div");
    item.className = "item";

    item.appendChild(
      createTextElement("div", "item-title", event.event_type)
    );
    item.appendChild(
      createTextElement("div", "item-meta", event.created_at)
    );

    const metadata = JSON.stringify(event.metadata);
    item.appendChild(
      createTextElement("div", "item-text", `${event.message}\n${metadata}`)
    );

    eventsList.appendChild(item);
  });
}

function renderWorkflows(workflows) {
  workflowsList.innerHTML = "";

  if (!workflows || workflows.length === 0) {
    workflowsList.textContent = "No workflows found.";
    workflowsList.className = "empty-state";
    return;
  }

  workflowsList.className = "";

  workflows.forEach((workflow) => {
    const item = document.createElement("div");
    item.className = "item";

    const title = createTextElement(
      "div",
      "item-title",
      `${workflow.workflow_id} — ${workflow.issue_type}`
    );

    const status = document.createElement("div");
    status.className = "item-meta";
    status.innerHTML = `
      Status:
      <span class="status-tag ${escapeHtml(workflow.status)}">
        ${escapeHtml(workflow.status)}
      </span>
      · Action: ${escapeHtml(workflow.recommended_action || "None")}
      · Transaction: ${escapeHtml(workflow.transaction_id || "None")}
    `;

    const text = createTextElement("div", "item-text", workflow.user_request);

    item.appendChild(title);
    item.appendChild(status);
    item.appendChild(text);

    workflowsList.appendChild(item);
  });
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with ${response.status}`);
  }

  return response.json();
}

async function loadWorkflowEvents(workflowId) {
  const events = await fetchJson(`/workflows/${workflowId}/events`);
  renderEvents(events);
}

async function refreshWorkflows() {
  const workflows = await fetchJson("/workflows");
  renderWorkflows(workflows);
}

async function submitSupportRequest(event) {
  event.preventDefault();

  const userRequest = userRequestInput.value.trim();

  if (!userRequest) {
    setError("Please enter a customer request.");
    return;
  }

  clearError();
  setStatus("Running", "loading");
  submitButton.disabled = true;
  answerText.textContent = "Running support workflow...";

  try {
    const data = await fetchJson("/support", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_request: userRequest,
        use_llm: useLlmInput.checked,
        confirm_action: confirmActionInput.checked,
      }),
    });

    answerText.textContent = data.answer;
    renderSecuritySummary(data);
    renderToolCalls(data.tool_calls);
    renderWorkflowSummary(data);

    if (data.workflow_id) {
      await loadWorkflowEvents(data.workflow_id);
    } else {
      eventsList.textContent = "No workflow events for this request.";
      eventsList.className = "empty-state";
    }

    await refreshWorkflows();

    setStatus("Success", "success");
  } catch (error) {
    setStatus("Error", "error");
    setError(error.message);
    answerText.textContent = "The request failed. Check the error message above.";
  } finally {
    submitButton.disabled = false;
  }
}

async function executeActiveWorkflow() {
  if (!activeWorkflowId) {
    setError("No active workflow selected.");
    return;
  }

  clearError();
  setStatus("Executing", "loading");
  executeWorkflowButton.disabled = true;

  try {
    const data = await fetchJson(`/workflows/${activeWorkflowId}/execute`, {
      method: "POST",
    });

    answerText.textContent = data.support_response.answer;
    renderSecuritySummary(data.support_response);
    renderToolCalls(data.support_response.tool_calls);
    renderWorkflowSummary(data.support_response);
    await loadWorkflowEvents(activeWorkflowId);
    await refreshWorkflows();

    setStatus("Completed", "success");
  } catch (error) {
    setStatus("Error", "error");
    setError(error.message);
  }
}

document.querySelectorAll(".example-chip").forEach((button) => {
  button.addEventListener("click", () => {
    userRequestInput.value = button.textContent;
  });
});

form.addEventListener("submit", submitSupportRequest);
executeWorkflowButton.addEventListener("click", executeActiveWorkflow);
refreshWorkflowsButton.addEventListener("click", refreshWorkflows);

refreshWorkflows().catch(() => {
  workflowsList.textContent = "Unable to load workflows yet.";
});