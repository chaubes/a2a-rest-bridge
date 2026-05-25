"""Guardrail checks for order tools.

Rules:
  * Every field required to create an order must be present (non-empty).
  * ``quantity`` must be a positive integer.
  * ``total_amount`` must be greater than 0.
"""

from __future__ import annotations

from numbers import Real

from shared.guardrails import GuardrailReport


def _is_nonempty(value: object) -> bool:
    if isinstance(value, str):
        return value.strip() != ""
    return value is not None


def check_create_order(
    customer_id: str,
    product_id: str,
    quantity: int,
    total_amount: float,
    currency: str,
    transaction_id: str,
    tracking_id: str,
) -> GuardrailReport:
    report = GuardrailReport()

    required = {
        "customer_id": customer_id,
        "product_id": product_id,
        "currency": currency,
        "transaction_id": transaction_id,
        "tracking_id": tracking_id,
    }
    for name, value in required.items():
        if _is_nonempty(value):
            report.add(f"{name}_present", True, "")
        else:
            report.add(f"{name}_present", False, f"{name} is required")

    if isinstance(quantity, bool) or not isinstance(quantity, int):
        report.add("quantity_valid", False, f"quantity must be an integer; got {quantity!r}")
    elif quantity > 0:
        report.add("quantity_valid", True, f"{quantity} is positive")
    else:
        report.add("quantity_valid", False, f"quantity {quantity} must be greater than 0")

    if isinstance(total_amount, bool) or not isinstance(total_amount, Real):
        report.add(
            "total_amount_positive",
            False,
            f"total_amount must be a number; got {total_amount!r}",
        )
    elif total_amount > 0:
        report.add("total_amount_positive", True, f"{total_amount} > 0")
    else:
        report.add(
            "total_amount_positive",
            False,
            f"total_amount {total_amount} must be greater than 0",
        )

    return report
