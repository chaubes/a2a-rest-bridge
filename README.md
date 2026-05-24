# AgentCart — Hybrid REST + A2A E-Commerce Demo

A working example of a **hybrid architecture** where deterministic REST APIs and
non-deterministic AI agents operate as partners. AgentCart implements a complete
e-commerce order-placement flow across three cooperating layers:

- **Layer 3 — REST APIs (Spring Boot / Java 21):** state mutations, ACID
  transactions, deterministic validation, and audit logging. These services do
  not know agents exist — a browser, a `curl` command, or an agent all hit the
  same validated endpoints.
- **Layer 2 — MCP tool servers (FastMCP / Python):** wrap each REST API as a
  typed tool, add agent-specific guardrails (amount ceilings, allowlists, rate
  limits), and translate HTTP responses into natural language.
- **Layer 1 — A2A agents (LangGraph + `a2a-sdk`):** handle customer
  interaction, intent extraction, cross-agent coordination, and workflow
  orchestration over the [Agent-to-Agent protocol](https://a2aproject.github.io/A2A/).

A React chat UI demonstrates the customer-facing agent placing orders from plain
natural language, with a side panel that surfaces the three-layer audit chain.

> This repository is the companion to the article *"The Great Rewiring"* and
> exists to show A2A and MCP working alongside production-grade REST services —
> not as a replacement for them.

## Architecture at a glance

```
React Chat UI  ──►  A2A Agents (LangGraph)  ──►  MCP Tool Servers (guardrails)  ──►  REST APIs (Spring Boot + H2)
   :3000              :10010–:10014                 :9001–:9005                        :8080–:8084
```

Every action a customer triggers flows top-to-bottom: an agent reasons about
intent, an MCP tool validates and translates the call, and a REST service
performs the actual, audited state change. A single `correlation_id` threads the
entire chain so any order can be traced across all three layers.

## Status

This project is built and run as a single stack via Docker Compose. Detailed
setup instructions, the demo walkthrough, and per-layer documentation live in
[`docs/`](docs/) and are completed as the stack comes together.

## License

Released under the [MIT License](LICENSE).
