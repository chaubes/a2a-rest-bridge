# AgentCart — MCP Tool Servers

This directory contains the **MCP (Model Context Protocol) tool layer** of
AgentCart. Each server wraps exactly one REST service, exposes its operations
as typed tools over Streamable HTTP, and adds the agent-facing concerns that do
not belong in the REST services themselves:

- **Guardrails** — input validation, allowlists, amount ceilings, and a
  per-correlation-id rate limit. Guardrails run **before** any REST call; a
  rejected call never touches the downstream service.
- **Natural-language translation** — every tool returns a plain-English string
  (not raw JSON) so a language-model agent can reason about the result, and
  failures include explicit guidance such as "Do NOT retry without checking
  status first".
- **Audit + tracing** — every call emits a structured JSON audit line to stdout
  and runs inside an OpenTelemetry span that carries the correlation id.

The REST services are deterministic and unaware of agents; this layer is the
narrow, validated waist between non-deterministic agents and those services.

## Servers and ports

| Server             | Port | Wraps REST service        | Default URL env var        |
| ------------------ | ---- | ------------------------- | -------------------------- |
| `inventory_mcp`    | 9001 | Inventory (`:8081`)       | `INVENTORY_SERVICE_URL`    |
| `payment_mcp`      | 9002 | Payment (`:8082`)         | `PAYMENT_SERVICE_URL`      |
| `shipping_mcp`     | 9003 | Shipping (`:8083`)        | `SHIPPING_SERVICE_URL`     |
| `order_mcp`        | 9004 | Order (`:8080`)           | `ORDER_SERVICE_URL`        |
| `notification_mcp` | 9005 | Notification (`:8084`)    | `NOTIFICATION_SERVICE_URL` |

Each server runs as an independent Streamable HTTP server bound to
`0.0.0.0` on its assigned port.

## Tools

### inventory_mcp (port 9001)
- `check_stock(product_id, quantity, correlation_id)`
- `reserve_stock(product_id, quantity, correlation_id)`
- `release_stock(product_id, quantity, correlation_id)`

Guardrails: `product_id` must match `^[A-Z]{2}-\d{3}$`; `quantity` is an
integer in `1..9999`.

### payment_mcp (port 9002)
- `charge_customer(customer_id, amount, currency, payment_method_token, correlation_id)`
- `check_transaction_status(transaction_id, correlation_id)`
- `refund_payment(transaction_id, correlation_id)`

Guardrails: `0 < amount <= 50000` (amounts above the ceiling require human
approval); `currency` in `{AUD, USD, EUR, GBP}`.

### shipping_mcp (port 9003)
- `create_shipment(order_id, address_line1, city, state, postcode, country, correlation_id)`
- `track_shipment(tracking_id, correlation_id)`

Guardrails: `country` in `{AU, US, UK, DE}`; address fields must be non-empty.

### order_mcp (port 9004)
- `create_order(customer_id, product_id, quantity, total_amount, currency, transaction_id, tracking_id, correlation_id)`
- `get_order(order_id, correlation_id)`

Guardrails: all fields required; `total_amount > 0`; `quantity > 0`.

### notification_mcp (port 9005)
- `send_notification(customer_id, message, channel, correlation_id)`

Guardrails: `channel` in `{email, sms}`; `len(message) <= 1000`.

## Correlation id

Every tool takes a `correlation_id`. It is forwarded to the REST service in
**both** the JSON body field `correlationId` and the `X-Correlation-ID`
header, threading a single action across the agent, MCP, and REST layers. The
shared rate limiter caps each correlation id at **100 tool calls per minute**.

## Configuration

Configuration is environment-only — there are no secrets in this layer. Each
server reads its REST base URL from the env var listed above, falling back to a
`http://localhost:<port>` default for local runs.

Tracing is configured by `OTEL_EXPORTER`:
- `console` (default) prints spans to stdout via the console exporter.
- `otlp` exports over gRPC to `OTEL_EXPORTER_OTLP_ENDPOINT`.

Outbound `httpx` requests are auto-instrumented so each REST call appears as a
child span of its tool span.

## Development

```bash
# from this directory
uv sync --extra dev        # resolve and install dependencies (Python 3.12)
uv run pytest -q           # run the guardrail and tool tests

# run an individual server (each blocks; ctrl-c to stop)
uv run python -m inventory_mcp.server
# or via the console script
uv run inventory-mcp
```

Console scripts are defined for every server: `inventory-mcp`, `payment-mcp`,
`shipping-mcp`, `order-mcp`, `notification-mcp`.

## Layout

```
mcp-servers/
  pyproject.toml
  shared/            audit, http client, correlation, tracing, rate limit, guardrail + runner helpers
  inventory_mcp/     server.py, guardrails.py, config.py
  payment_mcp/       ...
  shipping_mcp/      ...
  order_mcp/         ...
  notification_mcp/  ...
  tests/             guardrail unit tests + mocked-httpx tool tests
  Dockerfile.*       one slim image per server
```

## Docker

Each server has its own image, for example:

```bash
docker build -f Dockerfile.inventory -t agentcart-inventory-mcp .
docker run -p 9001:9001 \
  -e INVENTORY_SERVICE_URL=http://inventory-service:8081 \
  agentcart-inventory-mcp
```
