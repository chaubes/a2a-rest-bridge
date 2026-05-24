"""Notification A2A agent server."""

from __future__ import annotations

from a2a.types import AgentSkill

from notification_agent.config import HOST, PORT, public_url
from notification_agent.executor import build_executor
from shared.a2a_utils import build_agent_card, build_app
from shared.tracing import configure_langsmith

SKILLS = [
    AgentSkill(
        id="send_notification",
        name="Send notification",
        description=(
            "Send a customer notification over a channel (email/sms) via the "
            "notification service."
        ),
        tags=["notification", "messaging"],
        examples=[
            "Notify customer C-001 that order ORD-9 is confirmed via email, "
            "correlation_id=ord-1a2b3c4d",
        ],
    )
]


def build_agent_app():
    """Build the Starlette app for the notification agent."""
    configure_langsmith()
    card = build_agent_card(
        name="AgentCart Notification Agent",
        description="Bridges A2A tasks to the notification MCP tools.",
        url=public_url(),
        version="0.1.0",
        skills=SKILLS,
    )
    return build_app(agent_card=card, executor=build_executor())


def main() -> None:
    """Run the notification agent over HTTP."""
    import uvicorn

    uvicorn.run(build_agent_app(), host=HOST, port=PORT)


if __name__ == "__main__":
    main()
