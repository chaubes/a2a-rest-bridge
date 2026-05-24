"""Tool tests for payment_mcp with mocked httpx (respx)."""

from __future__ import annotations

import json

import httpx
import respx

from payment_mcp.config import settings
from payment_mcp.server import (
    charge_customer,
    check_transaction_status,
    refund_payment,
)

BASE = settings.payment_service_url
CID = "corr-pay-1"


@respx.mock
async def test_charge_200_success_translation_and_request_shape():
    route = respx.post(f"{BASE}/api/v1/payments/charge").mock(
        return_value=httpx.Response(
            200,
            json={
                "transactionId": "TX-100",
                "status": "SUCCESS",
                "amount": 199.5,
                "currency": "AUD",
                "timestamp": "2026-05-24T00:00:00Z",
            },
        )
    )
    result = await charge_customer(
        customer_id="CUST-1",
        amount=199.5,
        currency="AUD",
        payment_method_token="tok_secret",
        correlation_id=CID,
    )

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-Correlation-ID"] == CID
    body = json.loads(request.content)
    assert body == {
        "customerId": "CUST-1",
        "amount": 199.5,
        "currency": "AUD",
        "paymentMethodToken": "tok_secret",
        "correlationId": CID,
    }
    assert "Payment succeeded" in result
    assert "TX-100" in result


@respx.mock
async def test_charge_402_declined_no_retry():
    respx.post(f"{BASE}/api/v1/payments/charge").mock(
        return_value=httpx.Response(402, json={
            "timestamp": "t", "status": 402, "error": "Payment Required",
            "message": "card declined by issuer",
            "path": "/api/v1/payments/charge", "correlationId": CID,
        })
    )
    result = await charge_customer(
        customer_id="CUST-1",
        amount=10,
        currency="AUD",
        payment_method_token="tok",
        correlation_id=CID,
    )
    assert "DECLINED" in result
    assert "card declined by issuer" in result
    assert "Do NOT retry" in result


@respx.mock
async def test_charge_422_validation_surfaces_message():
    respx.post(f"{BASE}/api/v1/payments/charge").mock(
        return_value=httpx.Response(422, json={
            "timestamp": "t", "status": 422, "error": "Unprocessable Entity",
            "message": "amount must be positive",
            "path": "/api/v1/payments/charge", "correlationId": CID,
        })
    )
    result = await charge_customer(
        customer_id="CUST-1",
        amount=10,
        currency="AUD",
        payment_method_token="tok",
        correlation_id=CID,
    )
    assert "INVALID" in result
    assert "amount must be positive" in result


async def test_charge_over_ceiling_rejected_before_http():
    result = await charge_customer(
        customer_id="CUST-1",
        amount=50001,
        currency="AUD",
        payment_method_token="tok",
        correlation_id=CID,
    )
    assert result.startswith("REJECTED:")
    assert "human approval" in result.lower()


async def test_charge_bad_currency_rejected_before_http():
    result = await charge_customer(
        customer_id="CUST-1",
        amount=10,
        currency="JPY",
        payment_method_token="tok",
        correlation_id=CID,
    )
    assert result.startswith("REJECTED:")
    assert "currency_allowed" in result


@respx.mock
async def test_check_transaction_status_200():
    respx.get(f"{BASE}/api/v1/payments/transactions/TX-100").mock(
        return_value=httpx.Response(200, json={
            "transactionId": "TX-100", "customerId": "CUST-1",
            "amount": 199.5, "currency": "AUD", "status": "SUCCESS",
        })
    )
    result = await check_transaction_status(transaction_id="TX-100", correlation_id=CID)
    assert "TX-100" in result
    assert "SUCCESS" in result


@respx.mock
async def test_refund_200():
    route = respx.post(f"{BASE}/api/v1/payments/refund").mock(
        return_value=httpx.Response(200, json={"status": "REFUNDED"})
    )
    result = await refund_payment(transaction_id="TX-100", correlation_id=CID)
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body == {"transactionId": "TX-100", "correlationId": CID}
    assert "Refund processed" in result
