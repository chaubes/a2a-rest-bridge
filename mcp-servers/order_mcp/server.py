"""Order MCP tool server.

Wraps the order REST service (:8080) and exposes order creation and lookup as
MCP tools. Creating an order is the final step of the place-order workflow and
ties together the reserved stock, the payment transaction, and the shipment
tracking id under a single correlation id.
"""

from __future__ import annotations

from fastmcp import FastMCP

from order_mcp import guardrails
from order_mcp.config import PORT, SERVICE_NAME, settings
from shared.correlation import correlation_headers, with_correlation
from shared.guardrails import GuardrailReport
from shared.http_client import build_client, extract_error_message, safe_json
from shared.runner import run_tool
from shared.tracing import configure_tracing, traced_tool

configure_tracing(SERVICE_NAME)

mcp = FastMCP(SERVICE_NAME)


@mcp.tool
@traced_tool("create_order")
async def create_order(
    customer_id: str,
    product_id: str,
    quantity: int,
    total_amount: float,
    currency: str,
    transaction_id: str,
    tracking_id: str,
    correlation_id: str,
) -> str:
    """Create the final order record. Call this only after stock is reserved,
    payment has succeeded (transaction_id), and a shipment exists
    (tracking_id)."""
    report = guardrails.check_create_order(
        customer_id,
        product_id,
        quantity,
        total_amount,
        currency,
        transaction_id,
        tracking_id,
    )

    async def rest_call() -> str:
        body = with_correlation(
            {
                "customerId": customer_id,
                "productId": product_id,
                "quantity": quantity,
                "totalAmount": total_amount,
                "currency": currency,
                "transactionId": transaction_id,
                "trackingId": tracking_id,
            },
            correlation_id,
        )
        async with build_client(settings.order_service_url) as client:
            resp = await client.post(
                "/api/v1/orders",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code in (200, 201):
            data = safe_json(resp)
            return (
                f"Order created successfully. Order id is {data.get('orderId')} "
                f"(status {data.get('status')}) for customer '{customer_id}', "
                f"{quantity} x '{product_id}', total {total_amount} {currency}. "
                "The place-order workflow is complete."
            )
        return (
            f"FAILED to create the order for customer '{customer_id}': "
            f"{extract_error_message(resp)}. Do NOT retry without checking "
            "whether the order was already created; a duplicate order would "
            "double-bill the customer."
        )

    return await run_tool(
        tool="create_order",
        correlation_id=correlation_id,
        inputs={
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_amount": total_amount,
            "currency": currency,
            "transaction_id": transaction_id,
            "tracking_id": tracking_id,
        },
        guardrails=report,
        rest_call=rest_call,
    )


@mcp.tool
@traced_tool("get_order")
async def get_order(order_id: str, correlation_id: str) -> str:
    """Retrieve the current state of an order by its id."""
    report = GuardrailReport().add(
        "order_id_present",
        bool(order_id and str(order_id).strip()),
        "order_id must not be empty",
    )

    async def rest_call() -> str:
        async with build_client(settings.order_service_url) as client:
            resp = await client.get(
                f"/api/v1/orders/{order_id}",
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 404:
            return (
                f"No order found with id '{order_id}'. Verify the order id "
                "before retrying."
            )
        if resp.status_code != 200:
            return (
                f"FAILED to look up order '{order_id}': "
                f"{extract_error_message(resp)}."
            )
        data = safe_json(resp)
        return (
            f"Order '{order_id}' has status {data.get('status')} for customer "
            f"{data.get('customerId')}."
        )

    return await run_tool(
        tool="get_order",
        correlation_id=correlation_id,
        inputs={"order_id": order_id},
        guardrails=report,
        rest_call=rest_call,
    )


def main() -> None:
    """Run the order MCP server over Streamable HTTP."""
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
