"""Guardrail 5 (output): final-response consistency and redaction.

Runs on the assembled :class:`OrderConfirmation` before it is returned to the
caller. It confirms the response is internally consistent (the total billed
matches the amount actually charged, a confirmed order carries the identifiers
it should) and strips any sensitive field that must never leave the agent
boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Field names that must never appear in an outbound response payload.
SENSITIVE_FIELDS = {
    "payment_method_token",
    "paymentMethodToken",
    "token",
    "card_number",
    "cardNumber",
    "cvv",
}
_PENNY = 0.01


@dataclass
class OutputResult:
    """Outcome of an output-consistency evaluation."""

    passed: bool = True
    reasons: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.passed = False
        self.reasons.append(message)


def strip_sensitive(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-ish copy of ``payload`` with sensitive keys removed."""
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if key in SENSITIVE_FIELDS:
            continue
        if isinstance(value, dict):
            cleaned[key] = strip_sensitive(value)
        else:
            cleaned[key] = value
    return cleaned


def check_output(
    payload: dict[str, Any],
    *,
    amount_charged: float | None = None,
) -> OutputResult:
    """Validate a confirmation payload's internal consistency.

    * When ``amount_charged`` is known, it must equal ``total_amount``.
    * A ``confirmed`` order must carry a ``transaction_id``.
    * No sensitive field may be present in the payload.
    """
    result = OutputResult()

    if any(key in payload for key in SENSITIVE_FIELDS):
        result.fail("sensitive field present in outbound payload")

    status = payload.get("status")
    total = payload.get("total_amount")

    if (
        amount_charged is not None
        and total is not None
        and abs(float(total) - float(amount_charged)) > _PENNY
    ):
        result.fail(
            f"total_amount {total} does not match amount charged {amount_charged}"
        )

    if status == "confirmed" and not payload.get("transaction_id"):
        result.fail("confirmed order is missing a transaction_id")

    return result
