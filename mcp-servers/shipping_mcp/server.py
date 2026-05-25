"""Shipping MCP tool server.

Wraps the shipping REST service (:8083) and exposes shipment creation and
tracking as MCP tools. The shipping method defaults to STANDARD because the
tool surface intentionally keeps the agent-facing signature small; the REST
contract still receives the ``shippingMethod`` field.
"""

from __future__ import annotations

from fastmcp import FastMCP

from shared.correlation import correlation_headers, with_correlation
from shared.guardrails import GuardrailReport
from shared.http_client import build_client, extract_error_message, safe_json
from shared.runner import run_tool
from shared.tracing import configure_tracing, traced_tool
from shipping_mcp import guardrails
from shipping_mcp.config import PORT, SERVICE_NAME, settings

configure_tracing(SERVICE_NAME)

mcp = FastMCP(SERVICE_NAME)

DEFAULT_SHIPPING_METHOD = "STANDARD"


@mcp.tool
@traced_tool("create_shipment")
async def create_shipment(
    order_id: str,
    address_line1: str,
    city: str,
    state: str,
    postcode: str,
    country: str,
    correlation_id: str,
) -> str:
    """Create a shipment for an order that has already been placed. Returns a
    tracking id. Run only after the order has been created successfully."""
    report = guardrails.check_create_shipment(
        order_id, address_line1, city, state, postcode, country
    )

    async def rest_call() -> str:
        body = with_correlation(
            {
                "orderId": order_id,
                "addressLine1": address_line1,
                "city": city,
                "state": state,
                "postcode": postcode,
                "country": country,
                "shippingMethod": DEFAULT_SHIPPING_METHOD,
            },
            correlation_id,
        )
        async with build_client(settings.shipping_service_url) as client:
            resp = await client.post(
                "/api/v1/shipments",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code in (200, 201):
            data = safe_json(resp)
            return (
                f"Shipment created for order '{order_id}'. Tracking id is "
                f"{data.get('trackingId')} (status "
                f"{data.get('status', 'CREATED')}, method "
                f"{data.get('shippingMethod', DEFAULT_SHIPPING_METHOD)}). "
                f"Estimated delivery: {data.get('estimatedDelivery')}. Share "
                "the tracking id with the customer."
            )
        return (
            f"FAILED to create a shipment for order '{order_id}': "
            f"{extract_error_message(resp)}. Do NOT retry without checking "
            "whether a shipment already exists for this order."
        )

    return await run_tool(
        tool="create_shipment",
        correlation_id=correlation_id,
        inputs={
            "order_id": order_id,
            "address_line1": address_line1,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
        },
        guardrails=report,
        rest_call=rest_call,
    )


@mcp.tool
@traced_tool("track_shipment")
async def track_shipment(tracking_id: str, correlation_id: str) -> str:
    """Look up the current delivery status of a shipment by its tracking id."""
    report = GuardrailReport().add(
        "tracking_id_present",
        bool(tracking_id and str(tracking_id).strip()),
        "tracking_id must not be empty",
    )

    async def rest_call() -> str:
        async with build_client(settings.shipping_service_url) as client:
            resp = await client.get(
                f"/api/v1/shipments/{tracking_id}",
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 404:
            return (
                f"No shipment found with tracking id '{tracking_id}'. Verify "
                "the tracking id before retrying."
            )
        if resp.status_code != 200:
            return (
                f"FAILED to track shipment '{tracking_id}': "
                f"{extract_error_message(resp)}."
            )
        data = safe_json(resp)
        return (
            f"Shipment '{tracking_id}' for order {data.get('orderId')} has "
            f"status {data.get('status')}. Estimated delivery: "
            f"{data.get('estimatedDelivery')}."
        )

    return await run_tool(
        tool="track_shipment",
        correlation_id=correlation_id,
        inputs={"tracking_id": tracking_id},
        guardrails=report,
        rest_call=rest_call,
    )


def main() -> None:
    """Run the shipping MCP server over Streamable HTTP."""
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
