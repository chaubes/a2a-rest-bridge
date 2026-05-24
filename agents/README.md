# AgentCart — Agent Layer (Layer 1)

Five A2A agents that drive the AgentCart order workflow. This is the top layer
of a three-layer system:

- **Layer 1 (this package):** A2A agents (LangGraph + LangChain).
- **Layer 2:** FastMCP tool servers over Streamable HTTP.
- **Layer 3:** Spring Boot REST services.

## Agents and ports

| Agent              | Port  | Role                                                     |
| ------------------ | ----- | -------------------------------------------------------- |
| order-agent        | 10010 | Orchestrator. The frontend talks to this agent.          |
| inventory-agent    | 10011 | Thin A2A→MCP bridge to `inventory_mcp`.                  |
| payment-agent      | 10012 | Thin A2A→MCP bridge to `payment_mcp`.                    |
| shipping-agent     | 10013 | Thin A2A→MCP bridge to `shipping_mcp`.                   |
| notification-agent | 10014 | Thin A2A→MCP bridge to `notification_mcp`.               |

The Order Agent is an **A2A client** to the four peer agents and an **MCP
client** to `order_mcp` (for the `save_order` step). The peer agents each run a
small `create_react_agent` bound to their own MCP tools.

## Layout

```
agents/
  pyproject.toml  README.md  .python-version
  shared/            llm.py mcp_client.py a2a_utils.py peer_executor.py
                     guardrail_input.py guardrail_reasoning.py guardrail_output.py
                     audit.py correlation.py tracing.py
  order_agent/       server.py executor.py runtime.py graph.py state.py
                     prompts.py intent.py output_schemas.py config.py
  inventory_agent/   server.py executor.py graph.py prompts.py config.py
  payment_agent/     ...   shipping_agent/ ...   notification_agent/ ...
  tests/             test_intent_extraction.py test_output_validation.py
                     test_order_agent_graph.py test_guardrails.py
                     test_a2a_integration.py
  Dockerfile.order  Dockerfile.inventory  Dockerfile.payment
  Dockerfile.shipping  Dockerfile.notification
```

## Configuration (environment)

The LLM provider is selected by `LLM_PROVIDER` (`openai` default, or `ollama`).
All peer/MCP/agent URLs and the guardrail recursion limit are read from the
environment with sensible localhost defaults; see the repository's
`.env.example`. No secrets are hardcoded — the OpenAI key is only required when
actually constructing/using the OpenAI client.

Key variables: `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `OLLAMA_*`,
`AGENT_MAX_RECURSION_LIMIT`, `INVENTORY_MCP_URL` … `NOTIFICATION_MCP_URL`,
`ORDER_MCP_URL`, `INVENTORY_AGENT_URL` … `NOTIFICATION_AGENT_URL`,
`ORDER_AGENT_URL`, and `LANGSMITH_*`.

## Running

```bash
uv sync
uv run python -m order_agent.server           # :10010
uv run python -m inventory_agent.server        # :10011
# ... payment / shipping / notification likewise
```

Each agent serves its card at both `/.well-known/agent-card.json` (current A2A
path) and `/.well-known/agent.json` (legacy path), and the A2A JSON-RPC
endpoint at `/`.

## Order workflow

```
extract_intent
  → clarify                          (confidence < 0.90)
  → confirm_with_customer
  → check_inventory
      → format_response (failure)    (stock unavailable)
      → process_payment
          → arrange_shipping         (payment ok)
          → rollback_inventory       (payment failed) → format_response
  → save_order → send_notification → format_response → END
```

A correlation id (`ord-<8hex>`) is minted at the start and threaded through
every A2A task (as a `correlation_id=<id>` token in the message text) and MCP
call. Monetary totals are always computed in code as `unit_price * quantity`
from the in-context product catalog, never taken from the model.

## Guardrails

- **Guardrail 1 (input):** intent validation + confidence gate.
- **Guardrail 2 (reasoning):** plan sanity (never pay before reserving, never
  ship before paying) + recursion limit.
- **Guardrail 5 (output):** final-response consistency (total billed equals the
  amount charged) + stripping of sensitive fields (payment tokens).

Guardrails 3 and 4 live in the MCP and REST layers.

## Frontend contract

The browser frontend calls the **Order Agent** directly over A2A JSON-RPC. CORS
is permissive (`http://localhost:3000` and `*` by default; override with
`ORDER_AGENT_CORS_ORIGINS`).

Send a non-streaming `SendMessage` request:

```http
POST http://localhost:10010/
Content-Type: application/json
A2A-Version: 1.0
```

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [{ "text": "Order 2 Blue Widgets for Alice Johnson." }],
      "messageId": "<uuid>"
    }
  }
}
```

The response is a completed Task; the `OrderConfirmation` is the text of the
artifact named `order-confirmation`:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "task": {
      "id": "<task-uuid>",
      "contextId": "<ctx-uuid>",
      "status": { "state": "TASK_STATE_COMPLETED" },
      "artifacts": [
        {
          "artifactId": "<artifact-uuid>",
          "name": "order-confirmation",
          "parts": [{ "text": "{\"order_id\": \"ORD-42\", \"status\": \"confirmed\", ...}" }]
        }
      ]
    }
  }
}
```

Parse `result.task.artifacts[0].parts[0].text` as JSON to get the
`OrderConfirmation` (`order_id`, `status`, `customer_name`, `product_name`,
`quantity`, `unit_price`, `total_amount`, `currency`, `transaction_id`,
`tracking_id`, `estimated_delivery`, `failure_reason`, `correlation_id`).

The agent card advertises `streaming: false`, so use `SendMessage`. (The same
endpoint also accepts `SendStreamingMessage` for SSE if the card is later set to
`streaming: true`.)

## Tests

```bash
uv run pytest -q
```

The suite is fully offline: the LLM is faked, and the A2A peer client / order
MCP client are stubbed, so no network, model, or MCP server is required.
