"""A2A executor for the shipping agent."""

from __future__ import annotations

from shared.peer_executor import PeerAgentExecutor
from shipping_agent.config import AGENT_NAME, mcp_servers
from shipping_agent.prompts import SYSTEM_PROMPT


def build_executor() -> PeerAgentExecutor:
    """Construct the shipping agent's A2A executor."""
    return PeerAgentExecutor(
        agent_name=AGENT_NAME,
        mcp_servers=mcp_servers(),
        system_prompt=SYSTEM_PROMPT,
    )
