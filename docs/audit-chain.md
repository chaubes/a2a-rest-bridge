# Audit chain and tracing

Every order can be reconstructed end-to-end because a single `correlation_id`
threads through all three layers, and each layer emits its own structured log.
Together they form a three-layer audit chain; tracing adds timing and reasoning
on top.

## The correlation ID

The Order Agent generates a `correlation_id` (for example `ord-7721`) when a
workflow begins. From there it travels:

- in every **A2A task** the Order Agent sends to a peer agent,
- in every **MCP tool call** (as the `correlation_id` argument),
- on every **REST request** as the `X-Correlation-ID` header (and in the JSON
  body). If a request ever arrives without one, the REST layer generates a
  `gen-…` id so nothing is unattributed.

To follow a single order across the whole system, filter every log stream by its
`correlation_id`.

## Layer 1 — A2A task log

Emitted by the agents (`agents/shared/audit.py`) for each delegated task:

```json
{
  "layer": "a2a",
  "timestamp": "2026-05-21T10:30:01Z",
  "task_id": "t-9f3a",
  "from_agent": "order-agent",
  "to_agent": "payment-agent",
  "message_summary": "Charge customer C-001 amount 44.97 AUD",
  "status": "completed",
  "duration_ms": 1250,
  "correlation_id": "ord-7721"
}
```

## Layer 2 — MCP tool-call log

Emitted by each MCP server (`mcp-servers/shared/audit.py`). It records the
guardrail results and a summary of the translated response. Sensitive values
(such as payment tokens) are redacted:

```json
{
  "layer": "mcp",
  "timestamp": "2026-05-21T10:30:02Z",
  "tool": "charge_customer",
  "inputs": { "customer_id": "C-001", "amount": 44.97, "currency": "AUD" },
  "guardrail_results": [
    { "name": "amount_ceiling", "passed": true },
    { "name": "currency_allowlist", "passed": true }
  ],
  "output_summary": "Payment successful. Transaction ID: txn-8834",
  "status": "ok",
  "duration_ms": 800,
  "correlation_id": "ord-7721"
}
```

## Layer 3 — REST access log

Emitted by the Spring Boot services (`rest-services/common/.../AuditLogger.java`)
for every state mutation:

```json
{
  "layer": "rest",
  "timestamp": "2026-05-21T10:30:02Z",
  "service": "payment-service",
  "action": "CHARGE",
  "request": { "customerId": "C-001", "amount": 44.97, "currency": "AUD" },
  "response": { "transactionId": "txn-8834", "status": "SUCCESS" },
  "durationMs": 45,
  "correlation_id": "ord-7721"
}
```

All three are written as JSON to stdout, so under Docker Compose they are
collected by the standard logging driver. View one order's full chain with:

```bash
docker compose logs | grep ord-7721
```

## Tracing: timing and reasoning

The audit chain tells you *what* happened. Tracing tells you *how long* each step
took and *what the model was thinking*.

- **LangSmith** traces the agents natively — graph nodes, LLM calls, prompts,
  token usage, tool decisions, and state transitions. Enable it by setting
  `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`; LangGraph instruments itself
  automatically from those environment variables.
- **OpenTelemetry** traces the MCP → REST hop. Each tool call is wrapped in a
  span carrying `mcp.correlation_id`, and `httpx` is auto-instrumented so every
  REST request becomes a child span. The exporter is chosen by `OTEL_EXPORTER`
  (`console` by default, printing spans to stdout).

Because both systems carry the same `correlation_id`, you can pivot from a
LangSmith trace of the agent's reasoning to the OpenTelemetry spans for the
underlying tool and REST calls, and to the JSON audit records above — three
views of one order.
