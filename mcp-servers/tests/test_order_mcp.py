"""Tool tests for order_mcp with mocked httpx (respx)."""

from __future__ import annotations

import json

import httpx
import respx

from order_mcp.config import settings
from order_mcp.server import create_order, get_order

BASE = settings.order_service_url
CID = "corr-order-1"


@respx.mock
async def test_create_order_success_request_and_translation():
    route = respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(
            201, json={"orderId": "ORD-1", "status": "CONFIRMED"}
        )
    )
    result = await create_order(
        customer_id="CUST-1",
        product_id="AU-001",
        quantity=2,
        total_amount=199.5,
        currency="AUD",
        transaction_id="TX-1",
        tracking_id="TRK-1",
        correlation_id=CID,
    )

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-Correlation-ID"] == CID
    body = json.loads(request.content)
    assert body == {
        "customerId": "CUST-1",
        "productId": "AU-001",
        "quantity": 2,
        "totalAmount": 199.5,
        "currency": "AUD",
        "transactionId": "TX-1",
        "trackingId": "TRK-1",
        "correlationId": CID,
    }
    assert "Order created successfully" in result
    assert "ORD-1" in result


async def test_create_order_zero_amount_rejected_before_http():
    result = await create_order(
        customer_id="CUST-1",
        product_id="AU-001",
        quantity=2,
        total_amount=0,
        currency="AUD",
        transaction_id="TX-1",
        tracking_id="TRK-1",
        correlation_id=CID,
    )
    assert result.startswith("REJECTED:")
    assert "total_amount_positive" in result


@respx.mock
async def test_create_order_500_failure_warns_about_duplicates():
    respx.post(f"{BASE}/api/v1/orders").mock(
        return_value=httpx.Response(500, json={
            "timestamp": "t", "status": 500, "error": "Internal Server Error",
            "message": "database unavailable", "path": "/api/v1/orders",
            "correlationId": CID,
        })
    )
    result = await create_order(
        customer_id="CUST-1",
        product_id="AU-001",
        quantity=2,
        total_amount=10,
        currency="AUD",
        transaction_id="TX-1",
        tracking_id="TRK-1",
        correlation_id=CID,
    )
    assert "FAILED to create the order" in result
    assert "database unavailable" in result
    assert "Do NOT retry" in result


@respx.mock
async def test_get_order_200():
    respx.get(f"{BASE}/api/v1/orders/ORD-1").mock(
        return_value=httpx.Response(200, json={
            "orderId": "ORD-1", "customerId": "CUST-1", "status": "CONFIRMED",
        })
    )
    result = await get_order(order_id="ORD-1", correlation_id=CID)
    assert "ORD-1" in result
    assert "CONFIRMED" in result
