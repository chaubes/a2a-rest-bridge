"""Inventory MCP tool server.

Wraps the inventory REST service (:8081) and exposes stock lookup, reserve,
and release as MCP tools. Each tool runs guardrails first, forwards the
correlation id in both the JSON body and the ``X-Correlation-ID`` header, and
translates the HTTP response into natural language for the calling agent.
"""

from __future__ import annotations

from fastmcp import FastMCP

from inventory_mcp import guardrails
from inventory_mcp.config import PORT, SERVICE_NAME, settings
from shared.correlation import correlation_headers, with_correlation
from shared.http_client import build_client, extract_error_message, safe_json
from shared.runner import run_tool
from shared.tracing import configure_tracing, traced_tool

configure_tracing(SERVICE_NAME)

mcp = FastMCP(SERVICE_NAME)


@mcp.tool
@traced_tool("check_stock")
async def check_stock(product_id: str, quantity: int, correlation_id: str) -> str:
    """Look up current stock for a product and judge whether the requested
    quantity is available. Use this before attempting to reserve stock."""
    report = guardrails.check_product_and_quantity(product_id, quantity)

    async def rest_call() -> str:
        async with build_client(settings.inventory_service_url) as client:
            resp = await client.get(
                f"/api/v1/stock/{product_id}",
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 404:
            return (
                f"No product found with id '{product_id}'. The inventory "
                "service reported it does not exist. Do NOT retry; verify the "
                "product id before proceeding."
            )
        if resp.status_code != 200:
            return (
                f"FAILED to check stock for '{product_id}': "
                f"{extract_error_message(resp)}. "
                "Do NOT retry without checking the service status first."
            )
        body = safe_json(resp)
        available = body.get("availableQty")
        name = body.get("name", product_id)
        unit_price = body.get("unitPrice")
        if isinstance(available, int) and available >= quantity:
            return (
                f"Stock available: '{name}' ({product_id}) has {available} "
                f"units on hand, which covers the requested {quantity}. "
                f"Unit price is {unit_price}. It is safe to reserve."
            )
        return (
            f"Insufficient stock: '{name}' ({product_id}) has {available} "
            f"units available but {quantity} were requested. Do NOT attempt to "
            "reserve this quantity; reduce the quantity or choose another "
            "product."
        )

    return await run_tool(
        tool="check_stock",
        correlation_id=correlation_id,
        inputs={"product_id": product_id, "quantity": quantity},
        guardrails=report,
        rest_call=rest_call,
    )


@mcp.tool
@traced_tool("reserve_stock")
async def reserve_stock(product_id: str, quantity: int, correlation_id: str) -> str:
    """Reserve a quantity of a product so it cannot be sold to anyone else.
    Reserve only after confirming availability with check_stock."""
    report = guardrails.check_product_and_quantity(product_id, quantity)

    async def rest_call() -> str:
        body = with_correlation(
            {"productId": product_id, "quantity": quantity}, correlation_id
        )
        async with build_client(settings.inventory_service_url) as client:
            resp = await client.post(
                "/api/v1/stock/reserve",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 200:
            data = safe_json(resp)
            return (
                f"Reserved {data.get('reservedQty', quantity)} units of "
                f"'{product_id}'. Remaining available quantity is "
                f"{data.get('remainingQty')}. Status: "
                f"{data.get('status', 'RESERVED')}. Proceed to payment, then "
                "create the order with this product."
            )
        if resp.status_code == 409:
            return (
                f"Could not reserve {quantity} units of '{product_id}': "
                f"{extract_error_message(resp)}. There is not enough stock. Do "
                "NOT retry the same quantity; check stock again or lower the "
                "quantity."
            )
        return (
            f"FAILED to reserve stock for '{product_id}': "
            f"{extract_error_message(resp)}. Do NOT retry without checking the "
            "current stock status first."
        )

    return await run_tool(
        tool="reserve_stock",
        correlation_id=correlation_id,
        inputs={"product_id": product_id, "quantity": quantity},
        guardrails=report,
        rest_call=rest_call,
    )


@mcp.tool
@traced_tool("release_stock")
async def release_stock(product_id: str, quantity: int, correlation_id: str) -> str:
    """Release a previously reserved quantity back to available stock. Use
    this to compensate when a later step (payment, shipping) fails."""
    report = guardrails.check_product_and_quantity(product_id, quantity)

    async def rest_call() -> str:
        body = with_correlation(
            {"productId": product_id, "quantity": quantity}, correlation_id
        )
        async with build_client(settings.inventory_service_url) as client:
            resp = await client.post(
                "/api/v1/stock/release",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 200:
            data = safe_json(resp)
            return (
                f"Released {quantity} units of '{product_id}' back to stock. "
                f"Available quantity is now {data.get('availableQty')}. "
                f"Status: {data.get('status', 'RELEASED')}."
            )
        return (
            f"FAILED to release stock for '{product_id}': "
            f"{extract_error_message(resp)}. Do NOT retry without checking the "
            "current stock status first."
        )

    return await run_tool(
        tool="release_stock",
        correlation_id=correlation_id,
        inputs={"product_id": product_id, "quantity": quantity},
        guardrails=report,
        rest_call=rest_call,
    )


def main() -> None:
    """Run the inventory MCP server over Streamable HTTP."""
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
