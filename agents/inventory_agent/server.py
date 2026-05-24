"""Inventory A2A agent server.

Serves the agent card at the well-known path and the A2A JSON-RPC endpoint at
the app root, bridging inbound tasks to the inventory MCP tools.
"""

from __future__ import annotations

from a2a.types import AgentSkill

from inventory_agent.config import AGENT_NAME, HOST, PORT, public_url
from inventory_agent.executor import build_executor
from shared.a2a_utils import build_agent_card, build_app
from shared.tracing import configure_langsmith

SKILLS = [
    AgentSkill(
        id="manage_stock",
        name="Manage stock",
        description=(
            "Check, reserve, and release product stock via the inventory "
            "service. Accepts a natural-language instruction with a product id, "
            "quantity, and correlation id."
        ),
        tags=["inventory", "stock"],
        examples=[
            "Check stock for WB-001 quantity 2, correlation_id=ord-1a2b3c4d",
            "Reserve 1 unit of WR-001, correlation_id=ord-1a2b3c4d",
        ],
    )
]


def build_agent_app():
    """Build the Starlette app for the inventory agent."""
    configure_langsmith()
    card = build_agent_card(
        name="AgentCart Inventory Agent",
        description="Bridges A2A tasks to the inventory MCP tools.",
        url=public_url(),
        version="0.1.0",
        skills=SKILLS,
    )
    return build_app(agent_card=card, executor=build_executor())


def main() -> None:
    """Run the inventory agent over HTTP."""
    import uvicorn

    uvicorn.run(build_agent_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
