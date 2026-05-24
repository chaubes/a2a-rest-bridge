"""Guardrail checks for inventory tools.

Rules:
  * ``product_id`` must match ``^[A-Z]{2}-\\d{3}$`` (e.g. ``AU-001``).
  * ``quantity`` must be an integer in the inclusive range 1..9999.
"""

from __future__ import annotations

import re

from shared.guardrails import GuardrailReport

PRODUCT_ID_PATTERN = re.compile(r"^[A-Z]{2}-\d{3}$")
QUANTITY_MIN = 1
QUANTITY_MAX = 9999


def check_product_id(report: GuardrailReport, product_id: str) -> GuardrailReport:
    if isinstance(product_id, str) and PRODUCT_ID_PATTERN.match(product_id):
        report.add("product_id_format", True, "matches ^[A-Z]{2}-\\d{3}$")
    else:
        report.add(
            "product_id_format",
            False,
            f"product_id '{product_id}' must match the pattern AA-000 "
            "(two uppercase letters, a hyphen, three digits)",
        )
    return report


def check_quantity(report: GuardrailReport, quantity: int) -> GuardrailReport:
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        report.add(
            "quantity_range",
            False,
            f"quantity must be an integer; received {quantity!r}",
        )
    elif QUANTITY_MIN <= quantity <= QUANTITY_MAX:
        report.add("quantity_range", True, f"{quantity} is within 1..9999")
    else:
        report.add(
            "quantity_range",
            False,
            f"quantity {quantity} is outside the allowed range "
            f"{QUANTITY_MIN}..{QUANTITY_MAX}",
        )
    return report


def check_product_only(product_id: str) -> GuardrailReport:
    """Guardrails for tools that take only a product id (check_stock)."""
    return check_product_id(GuardrailReport(), product_id)


def check_product_and_quantity(product_id: str, quantity: int) -> GuardrailReport:
    """Guardrails for tools that take a product id and quantity."""
    report = GuardrailReport()
    check_product_id(report, product_id)
    check_quantity(report, quantity)
    return report
