"""Guardrail checks for payment tools.

Rules:
  * ``amount`` must satisfy ``0 < amount <= 50000``. Above the ceiling a human
    approval is required and the agent must not proceed autonomously.
  * ``currency`` must be one of {AUD, USD, EUR, GBP}.
"""

from __future__ import annotations

from numbers import Real

from shared.guardrails import GuardrailReport

AMOUNT_CEILING = 50000
ALLOWED_CURRENCIES = {"AUD", "USD", "EUR", "GBP"}


def check_amount(report: GuardrailReport, amount: float) -> GuardrailReport:
    if isinstance(amount, bool) or not isinstance(amount, Real):
        report.add(
            "amount_range",
            False,
            f"amount must be a number; received {amount!r}",
        )
    elif amount <= 0:
        report.add(
            "amount_range", False, f"amount {amount} must be greater than 0"
        )
    elif amount > AMOUNT_CEILING:
        report.add(
            "amount_ceiling",
            False,
            f"amount {amount} exceeds the autonomous ceiling of "
            f"{AMOUNT_CEILING}; human approval is required above {AMOUNT_CEILING}",
        )
    else:
        report.add("amount_range", True, f"{amount} is within (0, {AMOUNT_CEILING}]")
    return report


def check_currency(report: GuardrailReport, currency: str) -> GuardrailReport:
    if isinstance(currency, str) and currency in ALLOWED_CURRENCIES:
        report.add("currency_allowed", True, f"{currency} is supported")
    else:
        report.add(
            "currency_allowed",
            False,
            f"currency '{currency}' is not supported; allowed values are "
            f"{sorted(ALLOWED_CURRENCIES)}",
        )
    return report


def check_charge(amount: float, currency: str) -> GuardrailReport:
    report = GuardrailReport()
    check_amount(report, amount)
    check_currency(report, currency)
    return report
