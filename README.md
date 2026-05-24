# AgentCart — Hybrid REST + A2A E-Commerce Demo

A working example of a **hybrid architecture** where deterministic REST APIs and
non-deterministic AI agents operate as partners. AgentCart implements a complete
e-commerce order-placement flow — *"I'd like 3 blue widgets delivered to my
address"* — across three cooperating layers:

- **Layer 3 — REST APIs (Spring Boot / Java 21):** all state mutations, ACID
  transactions, deterministic validation, and audit logging. These services do
  not know agents exist — a browser, a `curl` command, or an agent all hit the
  same validated endpoints.
- **Layer 2 — MCP tool servers (FastMCP / Python):** wrap each REST API as a
  typed tool, add agent-specific guardrails (amount ceilings, allowlists, rate
  limits), and translate HTTP responses into natural language.
- **Layer 1 — A2A agents (LangGraph + `a2a-sdk`):** customer interaction, intent
  extraction, cross-agent coordination, and workflow orchestration over the
  [Agent-to-Agent protocol](https://a2aproject.github.io/A2A/).

A React chat UI demonstrates the customer-facing agent placing orders from plain
natural language, with a side panel that surfaces the three-layer audit chain.

> This repository is the companion to the article *"The Great Rewiring"* and
> exists to show A2A and MCP working **alongside** production-grade REST services
> — not as a replacement for them.

## Architecture at a glance

```
React Chat UI  ─►  A2A Agents (LangGraph)  ─►  MCP Tool Servers  ─►  REST APIs (Spring Boot + H2)
   :3000             :10010–:10014              :9001–:9005           :8080–:8084
                  reason & orchestrate        validate & translate   persist & audit
```

Every customer action flows top-to-bottom: an agent reasons about intent, an MCP
tool validates and translates the call, and a REST service performs the actual,
audited state change. A single `correlation_id` threads the whole chain, so any
order can be traced across all three layers. See [`docs/`](docs/) for the
[architecture](docs/architecture.md), [guardrails](docs/guardrails.md), and
[audit chain](docs/audit-chain.md) in depth.

## Prerequisites

- **Docker** and **Docker Compose** (the only hard requirement to run the stack).
- An **LLM** for the agents — either:
  - an **OpenAI API key** (default; uses `gpt-4o-mini`), or
  - a local **[Ollama](https://ollama.com)** install (set `LLM_PROVIDER=ollama`),
    so the demo runs with no cloud key or cost.

## Quick start

```bash
# 1. Configure environment (the only required value is your LLM provider)
cp .env.example .env
#    then edit .env: set OPENAI_API_KEY=sk-...   (or LLM_PROVIDER=ollama)

# 2. Build and start the whole stack
./scripts/run-all.sh
#    (equivalently: docker compose up --build)

# 3. Open the chat UI
open http://localhost:3000
```

The first build compiles Java, Python, and web images and takes a few minutes.
Startup is health-gated: REST services come up first, then their MCP servers,
then the agents, then the UI.

## Demo walkthrough

In the chat UI, try:

> *I am customer C-001. I'd like to order 3 Blue Widgets delivered to my default
> address. Please charge my card token tok-test-visa.*

The Order Agent extracts the intent, resolves the product and address, then
delegates across the Inventory, Payment, Shipping, and Notification agents and
returns a structured **order confirmation card**. Open the **audit panel** to
see the order's `correlation_id`.

Failure scenarios worth trying:

- *"I want 500 Widget Racks"* — only 25 exist; the order fails on the inventory
  check without charging anything.
- Order something for customer `DECLINE-TEST` — the payment is declined and the
  agent releases the stock reservation it had taken.

## Command-line tests

With the stack running:

```bash
./scripts/test-happy-path.sh      # natural-language order -> confirmed, verified in the REST services
./scripts/test-failure-paths.sh   # validation, decline, over-limit, and insufficient-stock paths
```

Per-layer unit tests:

```bash
( cd rest-services && ./gradlew test )   # JUnit 5 / MockMvc
( cd mcp-servers   && uv run pytest )    # guardrails + tool translation
( cd agents        && uv run pytest )    # intent, output, graph traversal, guardrails
```

## Project layout

```
rest-services/   Layer 3 — five Spring Boot services + a shared audit library
mcp-servers/     Layer 2 — five FastMCP tool servers + shared guardrail/audit/tracing code
agents/          Layer 1 — five A2A agents (Order Agent orchestrator + four peers)
frontend/        React + TypeScript + Tailwind chat UI
docs/            Architecture, guardrails, and audit-chain documentation
scripts/         run-all.sh and the integration test scripts
docker-compose.yml
```

## Configuration

All configuration is via environment variables; see [`.env.example`](.env.example).
Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model for the agents |
| `OPENAI_API_KEY` | — | required when `LLM_PROVIDER=openai` |
| `OLLAMA_MODEL` / `OLLAMA_BASE_URL` | `llama3.1` / local | used when `LLM_PROVIDER=ollama` |
| `LANGSMITH_TRACING` | `false` | enable LangSmith agent tracing |
| `OTEL_EXPORTER` | `console` | OpenTelemetry exporter for MCP→REST spans |

**`.env` is git-ignored and must never be committed** — only `.env.example`
(with placeholders) belongs in version control.

## Ports

| Layer | Service | Port |
|---|---|---|
| UI | Chat frontend | 3000 |
| REST | order / inventory / payment / shipping / notification | 8080 / 8081 / 8082 / 8083 / 8084 |
| MCP | inventory / payment / shipping / order / notification | 9001 / 9002 / 9003 / 9004 / 9005 |
| A2A | order / inventory / payment / shipping / notification | 10010 / 10011 / 10012 / 10013 / 10014 |

Each REST service also serves Swagger UI at `/swagger-ui.html` and health at
`/actuator/health`. Each agent serves its Agent Card at
`/.well-known/agent.json`.

## Notes

- The REST services use embedded **in-memory H2** seeded on startup, so the demo
  needs no external database. Data resets when the stack restarts — by design.
- Payments and shipping are deterministic mocks; no real money moves.

## License

Released under the [MIT License](LICENSE).
