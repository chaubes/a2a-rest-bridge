# Guardrails

Agent reasoning is non-deterministic. The way AgentCart stays reliable is by
constraining what an agent can actually *do* at five checkpoints spread across
the three layers. Each guardrail is independent: even if every other check were
bypassed, the REST layer still validates and the database still enforces its
constraints.

## Guardrail 1 — Input understanding
**Where:** Order Agent, intent-extraction step (`agents/order_agent/intent.py`).

The model extracts an `ExtractedOrderIntent` from the customer's message. Pydantic
then validates it:
- `quantity` must be 1–9999, `unit_price`/`total_amount` must be positive.
- `total_amount` is recomputed in code as `round(unit_price * quantity, 2)`; if
  the model's value disagrees, the code value wins. The model never decides money.
- `delivery_date`, if present, must be in the future.
- A `confidence_score` gates the workflow: below the threshold the agent asks a
  clarifying question instead of proceeding.

## Guardrail 2 — Agent reasoning
**Where:** Order Agent graph configuration (`agents/shared/guardrail_reasoning.py`).

- A `recursion_limit` (default 15, configurable via `AGENT_MAX_RECURSION_LIMIT`)
  prevents runaway loops.
- A plan-sanity check enforces ordering invariants — for example, payment is
  never attempted before stock is reserved, and shipping never precedes payment.

## Guardrail 3 — MCP tool validation
**Where:** every MCP tool server, before the REST call (`mcp-servers/*/guardrails.py`).

This is the trust boundary. Checks run *before* any HTTP request fires, so a
rejected call never reaches a REST API:
- **Payment:** amount must satisfy `0 < amount ≤ 50,000` (the agent ceiling —
  larger amounts require human approval); currency ∈ {AUD, USD, EUR, GBP}.
- **Inventory:** `product_id` must match `^[A-Z]{2}-\d{3}$`; quantity 1–9999.
- **Shipping:** country ∈ {AU, US, UK, DE}; address fields non-empty.
- **Notification:** channel ∈ {email, sms}; message ≤ 1000 characters.
- **Rate limit:** at most 100 tool calls per minute per `correlation_id`.

A rejection returns a clear `REJECTED: …` sentence to the agent and is recorded
in the MCP audit log with the failing check.

## Guardrail 4 — REST API validation
**Where:** every Spring Boot controller (`rest-services/*/dto/*.java`).

Jakarta Bean Validation annotations (`@NotNull`, `@Positive`, `@Pattern`,
`@DecimalMax`, `@Size`, …) validate every request body. Invalid input returns
HTTP 422 with the structured error contract. Business rules add more: a charge
over the single-transaction limit is declined (402), an over-reservation is
rejected (409). The database schema enforces the final layer of constraints.

## Guardrail 5 — Output response validation
**Where:** Order Agent, response formatting (`agents/shared/guardrail_output.py`).

Before the confirmation reaches the customer it is parsed into the
`OrderConfirmation` schema and checked for consistency — for instance, the
`total_amount` reported must equal the amount actually charged by the payment
service. Authoritative fields (status, IDs, amounts) are taken from workflow
state, not from the model's free text, and sensitive values such as payment
tokens are stripped. If parsing fails the agent retries once, then falls back to
building the confirmation deterministically from state.

## Why five and not one
Each layer guards a different failure mode:

| Guardrail | Catches |
|---|---|
| 1 Input | Misread intent, bad arithmetic, impossible dates |
| 2 Reasoning | Loops, out-of-order plans |
| 3 MCP | Out-of-policy actions (too large, wrong currency/country) |
| 4 REST | Malformed or rule-violating requests, bad state |
| 5 Output | Inconsistent or leaky responses |

Removing any one still leaves the others standing. That layering is what makes a
non-deterministic agent safe to put in front of real state changes.
