"""Tool tests for shipping_mcp with mocked httpx (respx)."""

from __future__ import annotations

import json

import httpx
import respx

from shipping_mcp.config import settings
from shipping_mcp.server import create_shipment, track_shipment

BASE = settings.shipping_service_url
CID = "corr-ship-1"


@respx.mock
async def test_create_shipment_success_request_and_translation():
    route = respx.post(f"{BASE}/api/v1/shipments").mock(
        return_value=httpx.Response(
            200,
            json={
                "trackingId": "TRK-9",
                "orderId": "ORD-1",
                "status": "CREATED",
                "estimatedDelivery": "2026-06-01",
                "shippingMethod": "STANDARD",
            },
        )
    )
    result = await create_shipment(
        order_id="ORD-1",
        address_line1="1 Smith St",
        city="Sydney",
        state="NSW",
        postcode="2000",
        country="AU",
        correlation_id=CID,
    )

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-Correlation-ID"] == CID
    body = json.loads(request.content)
    assert body["orderId"] == "ORD-1"
    assert body["country"] == "AU"
    assert body["correlationId"] == CID
    assert body["shippingMethod"] == "STANDARD"
    assert "Shipment created" in result
    assert "TRK-9" in result


async def test_create_shipment_bad_country_rejected_before_http():
    result = await create_shipment(
        order_id="ORD-1",
        address_line1="1 Smith St",
        city="Sydney",
        state="NSW",
        postcode="2000",
        country="FR",
        correlation_id=CID,
    )
    assert result.startswith("REJECTED:")
    assert "country_allowed" in result


@respx.mock
async def test_track_shipment_200():
    respx.get(f"{BASE}/api/v1/shipments/TRK-9").mock(
        return_value=httpx.Response(200, json={
            "trackingId": "TRK-9", "orderId": "ORD-1",
            "status": "IN_TRANSIT", "estimatedDelivery": "2026-06-01",
        })
    )
    result = await track_shipment(tracking_id="TRK-9", correlation_id=CID)
    assert "TRK-9" in result
    assert "IN_TRANSIT" in result
