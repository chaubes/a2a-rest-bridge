"""Payment MCP tool server.

Wraps the payment REST service (:8082) and exposes charge, status lookup, and
refund as MCP tools with amount/currency guardrails. The payment method token
is never written to the audit log (it is redacted by the shared logger).
"""

from __future__ import annotations

from fastmcp import FastMCP

from payment_mcp import guardrails
from payment_mcp.config import PORT, SERVICE_NAME, settings
from shared.correlation import correlation_headers, with_correlation
from shared.guardrails import GuardrailReport
from shared.http_client import build_client, extract_error_message, safe_json
from shared.runner import run_tool
from shared.tracing import configure_tracing, traced_tool

configure_tracing(SERVICE_NAME)

mcp = FastMCP(SERVICE_NAME)


@mcp.tool
@traced_tool("charge_customer")
async def charge_customer(
    customer_id: str,
    amount: float,
    currency: str,
    payment_method_token: str,
    correlation_id: str,
) -> str:
    """Charge a customer for an order. Run only after stock is reserved and
    the total amount is confirmed. Amounts above the ceiling are rejected and
    require human approval."""
    report = guardrails.check_charge(amount, currency)

    async def rest_call() -> str:
        body = with_correlation(
            {
                "customerId": customer_id,
                "amount": amount,
                "currency": currency,
                "paymentMethodToken": payment_method_token,
            },
            correlation_id,
        )
        async with build_client(settings.payment_service_url) as client:
            resp = await client.post(
                "/api/v1/payments/charge",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 200:
            data = safe_json(resp)
            return (
                f"Payment succeeded. Charged {data.get('amount', amount)} "
                f"{data.get('currency', currency)} to customer "
                f"'{customer_id}'. Transaction id is "
                f"{data.get('transactionId')} (status "
                f"{data.get('status', 'SUCCESS')}). Use this transaction id "
                "when creating the order."
            )
        if resp.status_code == 402:
            return (
                f"Payment DECLINED for customer '{customer_id}': "
                f"{extract_error_message(resp)}. Do NOT retry the same charge; "
                "the payment method was declined. Release any reserved stock "
                "and ask the customer for another payment method."
            )
        if resp.status_code == 422:
            return (
                f"Payment request was INVALID: {extract_error_message(resp)}. "
                "Do NOT retry without correcting the request fields."
            )
        return (
            f"FAILED to charge customer '{customer_id}': "
            f"{extract_error_message(resp)}. Do NOT retry without checking the "
            "transaction status first to avoid a double charge."
        )

    return await run_tool(
        tool="charge_customer",
        correlation_id=correlation_id,
        inputs={
            "customer_id": customer_id,
            "amount": amount,
            "currency": currency,
            "payment_method_token": payment_method_token,
        },
        guardrails=report,
        rest_call=rest_call,
    )


@mcp.tool
@traced_tool("check_transaction_status")
async def check_transaction_status(transaction_id: str, correlation_id: str) -> str:
    """Look up the current status of a payment transaction. Use this before
    retrying a charge to avoid double-charging a customer."""
    report = GuardrailReport().add(
        "transaction_id_present",
        bool(transaction_id and str(transaction_id).strip()),
        "transaction_id must not be empty",
    )

    async def rest_call() -> str:
        async with build_client(settings.payment_service_url) as client:
            resp = await client.get(
                f"/api/v1/payments/transactions/{transaction_id}",
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 404:
            return (
                f"No transaction found with id '{transaction_id}'. It was "
                "never recorded, so it is safe to attempt a new charge if "
                "needed."
            )
        if resp.status_code != 200:
            return (
                f"FAILED to look up transaction '{transaction_id}': "
                f"{extract_error_message(resp)}."
            )
        data = safe_json(resp)
        return (
            f"Transaction '{transaction_id}' has status "
            f"{data.get('status')} for customer {data.get('customerId')}, "
            f"amount {data.get('amount')} {data.get('currency')}."
        )

    return await run_tool(
        tool="check_transaction_status",
        correlation_id=correlation_id,
        inputs={"transaction_id": transaction_id},
        guardrails=report,
        rest_call=rest_call,
    )


@mcp.tool
@traced_tool("refund_payment")
async def refund_payment(transaction_id: str, correlation_id: str) -> str:
    """Refund a previously successful payment. Use this to compensate when a
    later step in the order fails after the charge has gone through."""
    report = GuardrailReport().add(
        "transaction_id_present",
        bool(transaction_id and str(transaction_id).strip()),
        "transaction_id must not be empty",
    )

    async def rest_call() -> str:
        body = with_correlation({"transactionId": transaction_id}, correlation_id)
        async with build_client(settings.payment_service_url) as client:
            resp = await client.post(
                "/api/v1/payments/refund",
                json=body,
                headers=correlation_headers(correlation_id),
            )
        if resp.status_code == 200:
            data = safe_json(resp)
            return (
                f"Refund processed for transaction '{transaction_id}' "
                f"(status {data.get('status', 'REFUNDED')}). The customer has "
                "been made whole."
            )
        return (
            f"FAILED to refund transaction '{transaction_id}': "
            f"{extract_error_message(resp)}. Do NOT retry without checking the "
            "transaction status first."
        )

    return await run_tool(
        tool="refund_payment",
        correlation_id=correlation_id,
        inputs={"transaction_id": transaction_id},
        guardrails=report,
        rest_call=rest_call,
    )


def main() -> None:
    """Run the payment MCP server over Streamable HTTP."""
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
