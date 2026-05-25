"""Configuration for the payment A2A agent (URLs from the environment)."""

from __future__ import annotations

import os

AGENT_NAME = "payment-agent"
PORT = 10012
HOST = "0.0.0.0"


def public_url() -> str:
    """Base URL this agent advertises in its AgentCard."""
    return os.getenv("PAYMENT_AGENT_URL", f"http://localhost:{PORT}")


def mcp_servers() -> dict[str, str]:
    """The MCP server(s) this agent is allowed to call."""
    return {"payment": os.getenv("PAYMENT_MCP_URL", "http://localhost:9002")}
