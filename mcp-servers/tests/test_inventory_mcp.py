"""Tool tests for inventory_mcp with mocked httpx (respx)."""

from __future__ import annotations

import httpx
import pytest
import respx

from inventory_mcp.config import settings
from inventory_mcp.server import check_stock, release_stock, reserve_stock

BASE = settings.inventory_service_url
CID = "corr-inv-1"


@respx.mock
async def test_check_stock_available_returns_safe_to_reserve():
    route = respx.get(f"{BASE}/api/v1/stock/AU-001").mock(
        return_value=httpx.Response(
            200,
            json={
                "productId": "AU-001",
                "name": "Widget",
                "unitPrice": 9.99,
                "availableQty": 50,
                "reservedQty": 0,
            },
        )
    )
    result = await check_stock(product_id="AU-001", quantity=5, correlation_id=CID)

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-Correlation-ID"] == CID
    assert "Stock available" in result
    assert "safe to reserve" in result


@respx.mock
async def test_check_stock_404_returns_not_found_guidance():
    respx.get(f"{BASE}/api/v1/stock/ZZ-999").mock(
        return_value=httpx.Response(404, json={
            "timestamp": "t", "status": 404, "error": "Not Found",
            "message": "product not found", "path": "/api/v1/stock/ZZ-999",
            "correlationId": CID,
        })
    )
    result = await check_stock(product_id="ZZ-999", quantity=1, correlation_id=CID)
    assert "No product found" in result
    assert "Do NOT retry" in result


@respx.mock
async def test_reserve_stock_200_translates_success_and_forwards_correlation():
    route = respx.post(f"{BASE}/api/v1/stock/reserve").mock(
        return_value=httpx.Response(
            200,
            json={
                "productId": "AU-001",
                "reservedQty": 3,
                "remainingQty": 47,
                "status": "RESERVED",
            },
        )
    )
    result = await reserve_stock(product_id="AU-001", quantity=3, correlation_id=CID)

    assert route.called
    request = route.calls.last.request
    # Correlation id forwarded in both header and body.
    assert request.headers["X-Correlation-ID"] == CID
    import json
    body = json.loads(request.content)
    assert body == {"productId": "AU-001", "quantity": 3, "correlationId": CID}
    assert "Reserved 3 units" in result
    assert "RESERVED" in result


@respx.mock
async def test_reserve_stock_409_returns_insufficient_no_retry():
    respx.post(f"{BASE}/api/v1/stock/reserve").mock(
        return_value=httpx.Response(409, json={
            "timestamp": "t", "status": 409, "error": "Conflict",
            "message": "insufficient stock: only 2 available",
            "path": "/api/v1/stock/reserve", "correlationId": CID,
        })
    )
    result = await reserve_stock(product_id="AU-001", quantity=99, correlation_id=CID)
    assert "Could not reserve" in result
    assert "insufficient stock: only 2 available" in result
    assert "Do NOT retry" in result


async def test_reserve_stock_guardrail_rejects_before_any_http_call():
    # No respx mock installed: if the tool tried to call the REST API it would
    # raise a connection error. A rejection means the call never happened.
    result = await reserve_stock(product_id="bad-id", quantity=5, correlation_id=CID)
    assert result.startswith("REJECTED:")
    assert "product_id_format" in result


async def test_reserve_stock_quantity_out_of_range_rejected():
    result = await reserve_stock(product_id="AU-001", quantity=0, correlation_id=CID)
    assert result.startswith("REJECTED:")
    assert "quantity_range" in result


@respx.mock
async def test_release_stock_200_translates_release():
    respx.post(f"{BASE}/api/v1/stock/release").mock(
        return_value=httpx.Response(
            200, json={"productId": "AU-001", "availableQty": 50, "status": "RELEASED"}
        )
    )
    result = await release_stock(product_id="AU-001", quantity=3, correlation_id=CID)
    assert "Released 3 units" in result
    assert "RELEASED" in result
