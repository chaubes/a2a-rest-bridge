"""Configuration for the notification A2A agent (URLs from the environment)."""

from __future__ import annotations

import os

AGENT_NAME = "notification-agent"
PORT = 10014
HOST = "0.0.0.0"


def public_url() -> str:
    """Base URL this agent advertises in its AgentCard."""
    return os.getenv("NOTIFICATION_AGENT_URL", f"http://localhost:{PORT}")


def mcp_servers() -> dict[str, str]:
    """The MCP server(s) this agent is allowed to call."""
    return {
        "notification": os.getenv(
            "NOTIFICATION_MCP_URL", "http://localhost:9005"
        )
    }
