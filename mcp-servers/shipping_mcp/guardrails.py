"""Guardrail checks for shipping tools.

Rules:
  * ``country`` must be one of {AU, US, UK, DE}.
  * All address fields supplied to create_shipment must be non-empty.
"""

from __future__ import annotations

from shared.guardrails import GuardrailReport

ALLOWED_COUNTRIES = {"AU", "US", "UK", "DE"}


def _is_nonempty(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def check_country(report: GuardrailReport, country: str) -> GuardrailReport:
    if isinstance(country, str) and country in ALLOWED_COUNTRIES:
        report.add("country_allowed", True, f"{country} is a supported destination")
    else:
        report.add(
            "country_allowed",
            False,
            f"country '{country}' is not supported; allowed values are "
            f"{sorted(ALLOWED_COUNTRIES)}",
        )
    return report


def check_create_shipment(
    order_id: str,
    address_line1: str,
    city: str,
    state: str,
    postcode: str,
    country: str,
) -> GuardrailReport:
    report = GuardrailReport()
    check_country(report, country)
    fields = {
        "order_id": order_id,
        "address_line1": address_line1,
        "city": city,
        "state": state,
        "postcode": postcode,
    }
    for name, value in fields.items():
        if _is_nonempty(value):
            report.add(f"{name}_present", True, "")
        else:
            report.add(f"{name}_present", False, f"{name} must not be empty")
    return report
