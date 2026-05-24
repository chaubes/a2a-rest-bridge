"""A2A executor for the inventory agent."""

from __future__ import annotations

from inventory_agent.config import AGENT_NAME, mcp_servers
from inventory_agent.prompts import SYSTEM_PROMPT
from shared.peer_executor import PeerAgentExecutor


def build_executor() -> PeerAgentExecutor:
    """Construct the inventory agent's A2A executor."""
    return PeerAgentExecutor(
        agent_name=AGENT_NAME,
        mcp_servers=mcp_servers(),
        system_prompt=SYSTEM_PROMPT,
    )
