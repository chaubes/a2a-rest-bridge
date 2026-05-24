"""Tool tests for notification_mcp with mocked httpx (respx)."""

from __future__ import annotations

import json

import httpx
import respx

from notification_mcp.config import settings
from notification_mcp.server import send_notification

BASE = settings.notification_service_url
CID = "corr-notif-1"


@respx.mock
async def test_send_notification_success_request_and_translation():
    route = respx.post(f"{BASE}/api/v1/notifications").mock(
        return_value=httpx.Response(
            200, json={"notificationId": "N-1", "status": "SENT", "channel": "email"}
        )
    )
    result = await send_notification(
        customer_id="CUST-1",
        message="Your order is confirmed",
        channel="email",
        correlation_id=CID,
    )

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-Correlation-ID"] == CID
    body = json.loads(request.content)
    assert body == {
        "customerId": "CUST-1",
        "message": "Your order is confirmed",
        "channel": "email",
        "correlationId": CID,
    }
    assert "Notification sent" in result
    assert "N-1" in result


async def test_send_notification_bad_channel_rejected_before_http():
    result = await send_notification(
        customer_id="CUST-1",
        message="hi",
        channel="push",
        correlation_id=CID,
    )
    assert result.startswith("REJECTED:")
    assert "channel_allowed" in result


async def test_send_notification_oversized_message_rejected_before_http():
    result = await send_notification(
        customer_id="CUST-1",
        message="x" * 1001,
        channel="email",
        correlation_id=CID,
    )
    assert result.startswith("REJECTED:")
    assert "message_length" in result
