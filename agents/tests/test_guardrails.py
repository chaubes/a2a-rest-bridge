"""Unit tests for the input, reasoning, and output guardrails."""

from __future__ import annotations

from dataclasses import dataclass

from shared.guardrail_input import CONFIDENCE_THRESHOLD, check_input_intent
from shared.guardrail_output import check_output, strip_sensitive
from shared.guardrail_reasoning import (
    check_plan,
    max_recursion_limit,
    within_recursion_budget,
)


@dataclass
class FakeIntent:
    product_id: str
    customer_id: str
    quantity: int
    total_amount: float
    confidence_score: float


PRODUCTS = {"WB-001", "WR-001"}
CUSTOMERS = {"C-001", "C-002"}


def test_input_guardrail_passes_high_confidence():
    intent = FakeIntent("WB-001", "C-001", 2, 29.98, 0.97)
    result = check_input_intent(
        intent, known_product_ids=PRODUCTS, known_customer_ids=CUSTOMERS
    )
    assert result.passed
    assert not result.needs_clarification


def test_input_guardrail_low_confidence_triggers_clarification():
    intent = FakeIntent("WB-001", "C-001", 2, 29.98, 0.5)
    result = check_input_intent(
        intent, known_product_ids=PRODUCTS, known_customer_ids=CUSTOMERS
    )
    assert result.needs_clarification


def test_input_guardrail_unknown_product_fails():
    intent = FakeIntent("ZZ-999", "C-001", 1, 10.0, 0.99)
    result = check_input_intent(
        intent, known_product_ids=PRODUCTS, known_customer_ids=CUSTOMERS
    )
    assert not result.passed
    assert any("product_id" in r for r in result.reasons)


def test_input_guardrail_unknown_customer_fails():
    intent = FakeIntent("WB-001", "C-999", 1, 10.0, 0.99)
    result = check_input_intent(
        intent, known_product_ids=PRODUCTS, known_customer_ids=CUSTOMERS
    )
    assert not result.passed


def test_threshold_is_ninety_percent():
    assert CONFIDENCE_THRESHOLD == 0.90


def test_reasoning_guardrail_accepts_safe_plan():
    plan = ["check_inventory", "process_payment", "arrange_shipping", "save_order"]
    assert check_plan(plan).passed


def test_reasoning_guardrail_rejects_payment_before_inventory():
    plan = ["process_payment", "check_inventory"]
    result = check_plan(plan)
    assert not result.passed
    assert any("payment" in r for r in result.reasons)


def test_reasoning_guardrail_rejects_shipping_before_payment():
    plan = ["check_inventory", "arrange_shipping"]
    result = check_plan(plan)
    assert not result.passed


def test_reasoning_guardrail_rejects_duplicate_step():
    plan = ["check_inventory", "check_inventory", "process_payment"]
    result = check_plan(plan)
    assert not result.passed


def test_recursion_budget(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_RECURSION_LIMIT", "5")
    assert max_recursion_limit() == 5
    assert within_recursion_budget(5)
    assert not within_recursion_budget(6)


def test_recursion_budget_default(monkeypatch):
    monkeypatch.delenv("AGENT_MAX_RECURSION_LIMIT", raising=False)
    assert max_recursion_limit() == 15


def test_recursion_budget_bad_value_defaults(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_RECURSION_LIMIT", "nonsense")
    assert max_recursion_limit() == 15


def test_output_guardrail_strips_and_checks():
    payload = strip_sensitive(
        {
            "status": "confirmed",
            "total_amount": 29.98,
            "transaction_id": "txn-1",
            "payment_method_token": "tok_secret",
        }
    )
    assert "payment_method_token" not in payload
    assert check_output(payload, amount_charged=29.98).passed
