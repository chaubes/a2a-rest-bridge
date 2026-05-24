"""Payment A2A agent server."""

from __future__ import annotations

from a2a.types import AgentSkill

from payment_agent.config import HOST, PORT, public_url
from payment_agent.executor import build_executor
from shared.a2a_utils import build_agent_card, build_app
from shared.tracing import configure_langsmith

SKILLS = [
    AgentSkill(
        id="process_payment",
        name="Process payment",
        description=(
            "Charge a customer, check a transaction's status, or refund a "
            "transaction via the payment service."
        ),
        tags=["payment", "billing"],
        examples=[
            "Charge customer C-001 amount 29.98 currency AUD with token "
            "tok_visa, correlation_id=ord-1a2b3c4d",
        ],
    )
]


def build_agent_app():
    """Build the Starlette app for the payment agent."""
    configure_langsmith()
    card = build_agent_card(
        name="AgentCart Payment Agent",
        description="Bridges A2A tasks to the payment MCP tools.",
        url=public_url(),
        version="0.1.0",
        skills=SKILLS,
    )
    return build_app(agent_card=card, executor=build_executor())


def main() -> None:
    """Run the payment agent over HTTP."""
    import uvicorn

    uvicorn.run(build_agent_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
