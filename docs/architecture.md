# Architecture

AgentCart is a hybrid system that places e-commerce orders from natural language.
It is built from three cooperating layers plus a chat UI. Each layer has a single,
clear responsibility, and the boundaries between them are where reliability is
enforced.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Customer chat UI (React)                                   :3000     │
│  natural language in, structured confirmation out                     │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  A2A / JSON-RPC over HTTP
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1 — A2A agents (LangGraph + a2a-sdk)            :10010–:10014  │
│                                                                       │
│   Order Agent ──A2A──► Inventory / Payment / Shipping / Notification  │
│   (orchestrator)        agents (thin A2A → MCP bridges)               │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  MCP tool calls (Streamable HTTP)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2 — MCP tool servers (FastMCP)                   :9001–:9005  │
│  guardrails (ceilings, allowlists, formats, rate limits)             │
│  + natural-language translation + audit + tracing                    │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │  HTTP + JSON (X-Correlation-ID)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3 — Spring Boot REST APIs (embedded H2)          :8080–:8084  │
│  Bean Validation · ACID writes · audit logging · OpenAPI             │
└─────────────────────────────────────────────────────────────────────┘
```

## Responsibilities

### Layer 3 — REST APIs (the reliable core)
Five Spring Boot services own all state. They validate input with Jakarta Bean
Validation, perform transactional writes against an embedded H2 database, and
emit a structured audit record for every mutation. They have no knowledge of
agents — the same endpoints serve a browser, a `curl` command, or an MCP tool
identically. This is the deterministic foundation everything else builds on.

| Service | Port | Responsibility |
|---|---|---|
| order-service | 8080 | Persist confirmed orders |
| inventory-service | 8081 | Stock levels, reserve / release |
| payment-service | 8082 | Charge / refund (deterministic mock) |
| shipping-service | 8083 | Create / track shipments (mock) |
| notification-service | 8084 | Record customer notifications (mock) |

### Layer 2 — MCP tool servers (the trust boundary)
Each REST service is wrapped by one FastMCP server that exposes its operations
as typed tools. Before any HTTP call is made, the MCP layer runs **guardrails**
— amount ceilings, currency and country allowlists, identifier-format checks,
quantity ranges, and a per-correlation rate limit. It then translates the REST
response into a natural-language sentence the agent can reason about, and logs
the call. The language model never reaches a REST API directly; every call
passes through schema validation and guardrail checks first.

| MCP server | Port | Wraps |
|---|---|---|
| inventory-mcp | 9001 | inventory-service |
| payment-mcp | 9002 | payment-service |
| shipping-mcp | 9003 | shipping-service |
| order-mcp | 9004 | order-service |
| notification-mcp | 9005 | notification-service |

### Layer 1 — A2A agents (the smart layer)
Five agents speak the [Agent-to-Agent protocol](https://a2aproject.github.io/A2A/).
Each publishes an Agent Card at `/.well-known/agent.json` and accepts tasks over
JSON-RPC. The **Order Agent** is the orchestrator: it extracts intent from the
customer's message, confirms its interpretation, then delegates each step to a
specialised peer agent over A2A. The peer agents (inventory, payment, shipping,
notification) are deliberately thin — they translate an A2A task into the right
MCP tool call and return the result.

| Agent | Port | Role |
|---|---|---|
| order-agent | 10010 | Orchestrate the full order workflow |
| inventory-agent | 10011 | Check / reserve / release stock via MCP |
| payment-agent | 10012 | Charge / refund via MCP |
| shipping-agent | 10013 | Create / track shipments via MCP |
| notification-agent | 10014 | Send notifications via MCP |

## Order workflow

The Order Agent runs a LangGraph state machine:

```
extract_intent → confirm_with_customer → check_inventory → process_payment
                                                                  │
                                          ┌───────────────────────┴───────────┐
                                   payment ok                          payment failed
                                          │                                   │
                                   arrange_shipping                   rollback_inventory
                                          │                                   │
                                     save_order                          handle_failure
                                          │                                   │
                                   send_notification                        END
                                          │
                                   format_response → END
```

- Intent extraction is gated by a confidence score; low confidence routes to a
  clarifying question instead of acting.
- Money is always computed in code from the catalog `unit_price`, never taken
  from the model's arithmetic.
- If payment fails after stock was reserved, the agent releases the reservation
  (`rollback_inventory`) before reporting failure — no orphaned holds.

## Cross-cutting concerns
- **Correlation ID:** a single `correlation_id` (e.g. `ord-7721`) is generated at
  the start of each workflow and threaded through every A2A task, MCP tool call,
  and REST request (`X-Correlation-ID`). See [audit-chain.md](audit-chain.md).
- **Guardrails:** five validation checkpoints across the three layers. See
  [guardrails.md](guardrails.md).
- **Configurable LLM:** the agents default to OpenAI `gpt-4o-mini` but can run
  fully locally against Ollama by setting `LLM_PROVIDER=ollama`.

## Running it
Everything is orchestrated by `docker-compose.yml`. Startup order is enforced
with health checks: REST services start first, then their MCP servers, then the
agents, then the UI. See the top-level [README](../README.md) for instructions.
