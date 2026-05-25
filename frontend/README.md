# AgentCart — Chat UI

The customer-facing chat frontend for the AgentCart order agent. Built with React 18, TypeScript, Vite, and Tailwind CSS.

## Overview

This single-page application lets customers place orders through a natural-language conversation. It communicates with the A2A Order Agent over JSON-RPC 2.0 and renders structured order confirmations alongside the agent's text replies.

## Development

```bash
npm install
npm run dev          # dev server on :3000
npm run build        # production build → dist/
npm run typecheck    # type-check only (no emit)
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `VITE_ORDER_AGENT_URL` | `http://localhost:10010` | Base URL of the A2A Order Agent |

Create a `.env.local` file to override:

```
VITE_ORDER_AGENT_URL=http://localhost:10010
```

## Docker

```bash
# Build image (bakes VITE_ORDER_AGENT_URL at build time)
docker build \
  --build-arg VITE_ORDER_AGENT_URL=http://localhost:10010 \
  -t agentcart-ui .

# Run
docker run -p 3000:3000 agentcart-ui
```

The container serves the static build via nginx on port **3000** with SPA fallback.

## Project structure

```
src/
  api/orderAgent.ts        — JSON-RPC request/response handling
  hooks/useChat.ts         — conversation state management
  types/index.ts           — shared TypeScript types
  components/
    ChatWindow.tsx          — message list + input form
    MessageBubble.tsx       — user / assistant bubble
    OrderConfirmationCard.tsx — structured order result card
    TypingIndicator.tsx     — animated dots while agent is thinking
    AuditTrailPanel.tsx     — collapsible correlation ID + step trace
```

## A2A protocol notes

Requests go to `POST {VITE_ORDER_AGENT_URL}/` with a JSON-RPC 2.0 body. On the first turn only `message.parts` are sent. Subsequent turns include `taskId` and/or `contextId` from the previous response to maintain conversation continuity.

The client extracts `OrderConfirmation` data from two locations:

1. Fenced ` ```json ``` ` blocks inside text parts (most common)
2. Structured `data` parts where `part.kind === "data"`

If neither is present the plain text reply is shown on its own.
