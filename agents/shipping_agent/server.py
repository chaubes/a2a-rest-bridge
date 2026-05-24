"""Shipping A2A agent server."""

from __future__ import annotations

from a2a.types import AgentSkill

from shared.a2a_utils import build_agent_card, build_app
from shared.tracing import configure_langsmith
from shipping_agent.config import HOST, PORT, public_url
from shipping_agent.executor import build_executor

SKILLS = [
    AgentSkill(
        id="arrange_shipping",
        name="Arrange shipping",
        description=(
            "Create a shipment for an order and track existing shipments via "
            "the shipping service."
        ),
        tags=["shipping", "logistics"],
        examples=[
            "Create a shipment for order ORD-9 to 100 George St, Sydney NSW "
            "2000, AU, correlation_id=ord-1a2b3c4d",
        ],
    )
]


def build_agent_app():
    """Build the Starlette app for the shipping agent."""
    configure_langsmith()
    card = build_agent_card(
        name="AgentCart Shipping Agent",
        description="Bridges A2A tasks to the shipping MCP tools.",
        url=public_url(),
        version="0.1.0",
        skills=SKILLS,
    )
    return build_app(agent_card=card, executor=build_executor())


def main() -> None:
    """Run the shipping agent over HTTP."""
    import uvicorn

    uvicorn.run(build_agent_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
