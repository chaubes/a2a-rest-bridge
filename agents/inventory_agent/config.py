"""Configuration for the inventory A2A agent (URLs from the environment)."""

from __future__ import annotations

import os

AGENT_NAME = "inventory-agent"
PORT = 10011
HOST = "0.0.0.0"


def public_url() -> str:
    """Base URL this agent advertises in its AgentCard."""
    return os.getenv("INVENTORY_AGENT_URL", f"http://localhost:{PORT}")


def mcp_servers() -> dict[str, str]:
    """The MCP server(s) this agent is allowed to call."""
    return {"inventory": os.getenv("INVENTORY_MCP_URL", "http://localhost:9001")}
