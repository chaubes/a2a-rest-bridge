"""Order A2A agent server (the orchestrator the frontend talks to).

Serves the agent card and the A2A JSON-RPC endpoint, with permissive CORS so
the browser frontend at http://localhost:3000 can call it directly.
"""

from __future__ import annotations

import os

from a2a.types import AgentSkill

from order_agent.config import HOST, PORT, public_url
from order_agent.executor import build_executor
from shared.a2a_utils import build_agent_card, build_app
from shared.tracing import configure_langsmith

SKILLS = [
    AgentSkill(
        id="place_order",
        name="Place an order",
        description=(
            "Orchestrate an end-to-end order: understand the request, reserve "
            "stock, charge the customer, arrange shipping, persist the order, "
            "and notify the customer. Returns an OrderConfirmation."
        ),
        tags=["orders", "checkout", "orchestration"],
        examples=[
            "Order 2 Blue Widgets for Alice Johnson.",
            "I'd like 1 Widget Rack delivered to Bob Smith.",
        ],
    )
]


def _cors_origins() -> list[str]:
    """Allowed CORS origins; defaults to the local frontend plus wildcard."""
    raw = os.getenv("ORDER_AGENT_CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return ["http://localhost:3000", "*"]


def build_agent_app():
    """Build the Starlette app for the order agent (with CORS)."""
    configure_langsmith()
    card = build_agent_card(
        name="AgentCart Order Agent",
        description=(
            "Orchestrates the AgentCart order workflow across the inventory, "
            "payment, shipping, and notification agents."
        ),
        url=public_url(),
        version="0.1.0",
        skills=SKILLS,
    )
    return build_app(
        agent_card=card,
        executor=build_executor(),
        cors_origins=_cors_origins(),
    )


def main() -> None:
    """Run the order agent over HTTP."""
    import uvicorn

    uvicorn.run(build_agent_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
