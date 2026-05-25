"""Notification MCP tool server.

Wraps the notification REST service (:8084) and exposes a single tool for
sending a customer notification over a supported channel.
"""

from __future__ import annotations

from fastmcp import FastMCP

from notification_mcp import guardrails
from notification_mcp.config import PORT, SERVICE_NAME, settings
from shared.correlation import correlation_headers, with_correlation
from shared.http_client import build_client, extract_error_message, safe_json
from shared.runner import run_tool
from shared.tracing import configure_tracing, traced_tool

configure_tracing(SERVICE_NAME)

mcp = FastMCP(SERVICE_NAME)


@mcp.tool
@traced_tool("send_notification")
async def send_notification(
    customer_id: str, message: str, channel: str, correlation_id: str
) -> str:
    """Send a notification to a customer over email or sms. Use this to confirm
    an order or to inform the customer of a failure."""
    report = guardrails.check_send_notification(message, channel)

    async def rest_call() -> str:
        body = with_correlation(
            {"customerId": customer_id, "message": message, "channel": channel},
            correlation_id,
        )
        async with build_client(settings.notification_service_url) as client:
            resp = await client.post(
                "/api/v1/notifications",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code in (200, 201):
            data = safe_json(resp)
            return (
                f"Notification sent to customer '{customer_id}' over "
                f"{data.get('channel', channel)} (id "
                f"{data.get('notificationId')}, status "
                f"{data.get('status', 'SENT')})."
            )
        return (
            f"FAILED to send a notification to customer '{customer_id}': "
            f"{extract_error_message(resp)}. A failed notification is not "
            "fatal to the order; do not block the workflow on it."
        )

    return await run_tool(
        tool="send_notification",
        correlation_id=correlation_id,
        inputs={
            "customer_id": customer_id,
            "message": message,
            "channel": channel,
        },
        guardrails=report,
        rest_call=rest_call,
    )


def main() -> None:
    """Run the notification MCP server over Streamable HTTP."""
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
