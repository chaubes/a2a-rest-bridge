"""Runtime wiring for the order agent's real (non-test) dependencies.

Builds the :class:`OrderGraphDeps` used in production: the configured LLM, a
peer caller that speaks A2A to the four peer agents, and an order saver that
invokes the order MCP ``create_order`` tool directly.
"""

from __future__ import annotations

import logging

from order_agent import config
from order_agent.graph import OrderGraphDeps
from shared.a2a_utils import call_peer_agent
from shared.llm import make_llm
from shared.mcp_client import load_mcp_tools

logger = logging.getLogger("agentcart.order.runtime")


def _make_peer_caller():
    peers = config.peer_urls()

    async def call_peer(peer_name: str, message_text: str) -> str:
        url = peers[peer_name]
        return await call_peer_agent(url, message_text)

    return call_peer


def _make_order_saver():
    _cache: dict[str, object] = {}

    async def _get_tool():
        if "create_order" not in _cache:
            tools = await load_mcp_tools(config.order_mcp_servers())
            by_name = {t.name: t for t in tools}
            tool = by_name.get("create_order")
            if tool is None:
                raise RuntimeError(
                    "order MCP does not expose a 'create_order' tool"
                )
            _cache["create_order"] = tool
        return _cache["create_order"]

    async def save_order(
        *,
        customer_id,
        product_id,
        quantity,
        total_amount,
        currency,
        transaction_id,
        tracking_id,
        correlation_id,
    ) -> str:
        tool = await _get_tool()
        result = await tool.ainvoke(
            {
                "customer_id": customer_id,
                "product_id": product_id,
                "quantity": quantity,
                "total_amount": total_amount,
                "currency": currency,
                "transaction_id": transaction_id,
                "tracking_id": tracking_id,
                "correlation_id": correlation_id,
            }
        )
        return result if isinstance(result, str) else str(result)

    return save_order


def build_deps() -> OrderGraphDeps:
    """Assemble the production dependencies for the order workflow graph."""
    return OrderGraphDeps(
        llm=make_llm(),
        call_peer=_make_peer_caller(),
        save_order=_make_order_saver(),
    )
