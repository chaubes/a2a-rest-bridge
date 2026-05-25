"""Tests for OrderConfirmation parsing, fallback, and sensitive-field stripping."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from order_agent.graph import _deterministic_confirmation
from order_agent.output_schemas import OrderConfirmation
from shared.guardrail_output import check_output, strip_sensitive

CONFIRMED = {
    "order_id": "ORD-9",
    "status": "confirmed",
    "customer_name": "Alice Johnson",
    "product_name": "Blue Widget",
    "quantity": 2,
    "unit_price": 14.99,
    "total_amount": 29.98,
    "currency": "AUD",
    "transaction_id": "txn-abc123",
    "tracking_id": "trk-xyz789",
    "correlation_id": "ord-1a2b3c4d",
}


def test_order_confirmation_parses():
    conf = OrderConfirmation(**CONFIRMED)
    assert conf.status == "confirmed"
    assert conf.transaction_id == "txn-abc123"


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        OrderConfirmation(**dict(CONFIRMED, status="bogus"))


def test_deterministic_fallback_from_state():
    state = {
        "order_id": "ORD-9",
        "status": "confirmed",
        "customer_name": "Alice Johnson",
        "product_name": "Blue Widget",
        "quantity": 2,
        "unit_price": 14.99,
        "total_amount": 29.98,
        "currency": "AUD",
        "transaction_id": "txn-abc123",
        "tracking_id": "trk-xyz789",
        "payment_ok": True,
        "correlation_id": "ord-1a2b3c4d",
    }
    conf = _deterministic_confirmation(state)
    assert conf.order_id == "ORD-9"
    assert conf.status == "confirmed"
    assert conf.total_amount == pytest.approx(29.98)


def test_fallback_infers_failed_status_when_payment_missing():
    state = {
        "correlation_id": "ord-deadbeef",
        "payment_ok": False,
        "failure_reason": "Payment declined",
    }
    conf = _deterministic_confirmation(state)
    assert conf.status == "failed"
    assert conf.failure_reason == "Payment declined"


def test_strip_sensitive_removes_tokens_nested():
    payload = {
        "order_id": "ORD-9",
        "payment_method_token": "tok_secret",
        "nested": {"token": "abc", "ok": 1},
    }
    cleaned = strip_sensitive(payload)
    assert "payment_method_token" not in cleaned
    assert "token" not in cleaned["nested"]
    assert cleaned["nested"]["ok"] == 1


def test_output_guardrail_flags_amount_mismatch():
    result = check_output(
        strip_sensitive(CONFIRMED), amount_charged=99.99
    )
    assert not result.passed
    assert any("total_amount" in r for r in result.reasons)


def test_output_guardrail_passes_when_consistent():
    result = check_output(strip_sensitive(CONFIRMED), amount_charged=29.98)
    assert result.passed


def test_output_guardrail_flags_confirmed_without_transaction():
    payload = dict(CONFIRMED, transaction_id=None)
    result = check_output(strip_sensitive(payload), amount_charged=29.98)
    assert not result.passed


def test_output_guardrail_flags_present_sensitive_field():
    payload = dict(CONFIRMED, token="leak")
    result = check_output(payload, amount_charged=29.98)
    assert not result.passed
