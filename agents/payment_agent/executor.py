"""A2A executor for the payment agent."""

from __future__ import annotations

from payment_agent.config import AGENT_NAME, mcp_servers
from payment_agent.prompts import SYSTEM_PROMPT
from shared.peer_executor import PeerAgentExecutor


def build_executor() -> PeerAgentExecutor:
    """Construct the payment agent's A2A executor."""
    return PeerAgentExecutor(
        agent_name=AGENT_NAME,
        mcp_servers=mcp_servers(),
        system_prompt=SYSTEM_PROMPT,
    )
