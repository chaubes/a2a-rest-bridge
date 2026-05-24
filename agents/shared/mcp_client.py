"""MCP client helpers built on ``langchain-mcp-adapters``.

Each peer agent owns exactly one MCP server; the Order Agent additionally
talks to the order MCP directly for the ``save_order`` step. These helpers
build a :class:`MultiServerMCPClient` over the Streamable HTTP transport and
load the remote MCP tools as LangChain tools.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

# FastMCP serves the Streamable HTTP endpoint under ``/mcp`` by default.
DEFAULT_MCP_PATH = "/mcp"


def _normalise(url: str) -> str:
    """Ensure the configured base URL points at the ``/mcp`` endpoint."""
    url = url.rstrip("/")
    if url.endswith(DEFAULT_MCP_PATH):
        return url
    return url + DEFAULT_MCP_PATH


def build_mcp_client(servers: dict[str, str]) -> MultiServerMCPClient:
    """Create a multi-server MCP client.

    ``servers`` maps a logical name (e.g. ``"inventory"``) to the base URL of
    its MCP server. The Streamable HTTP transport is used for every server.
    """
    connections = {
        name: {"transport": "streamable_http", "url": _normalise(url)}
        for name, url in servers.items()
    }
    return MultiServerMCPClient(connections)


async def load_mcp_tools(servers: dict[str, str]) -> list[BaseTool]:
    """Build a client and load every remote tool as a LangChain tool."""
    client = build_mcp_client(servers)
    return await client.get_tools()
