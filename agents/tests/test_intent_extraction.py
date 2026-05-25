"""Tests for ExtractedOrderIntent validation and its business validators."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from order_agent.intent import ExtractedOrderIntent

BASE = {
    "product_id": "WB-001",
    "product_name": "Blue Widget",
    "quantity": 2,
    "unit_price": 14.99,
    "total_amount": 29.98,
    "shipping_method": "standard",
    "customer_id": "C-001",
    "address": {"line1": "100 George St", "city": "Sydney"},
    "confidence_score": 0.95,
}


def test_valid_intent_round_trips():
    intent = ExtractedOrderIntent(**BASE)
    assert intent.product_id == "WB-001"
    assert intent.total_amount == pytest.approx(29.98)


def test_total_amount_override_corrects_bad_arithmetic():
    bad = dict(BASE, total_amount=999.99)  # LLM got the math wrong
    intent = ExtractedOrderIntent(**bad)
    # Validator must override with unit_price * quantity.
    assert intent.total_amount == pytest.approx(round(14.99 * 2, 2))


def test_total_amount_kept_when_within_one_cent():
    near = dict(BASE, total_amount=29.975)  # within a cent of 29.98
    intent = ExtractedOrderIntent(**near)
    assert intent.total_amount == pytest.approx(29.975)


def test_future_delivery_date_accepted():
    future = (date.today() + timedelta(days=5)).isoformat()
    intent = ExtractedOrderIntent(**dict(BASE, delivery_date=future))
    assert intent.delivery_date == future


def test_past_delivery_date_rejected():
    past = (date.today() - timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        ExtractedOrderIntent(**dict(BASE, delivery_date=past))


def test_today_delivery_date_rejected():
    today = date.today().isoformat()
    with pytest.raises(ValidationError):
        ExtractedOrderIntent(**dict(BASE, delivery_date=today))


def test_malformed_delivery_date_rejected():
    with pytest.raises(ValidationError):
        ExtractedOrderIntent(**dict(BASE, delivery_date="not-a-date"))


def test_quantity_bounds_enforced():
    with pytest.raises(ValidationError):
        ExtractedOrderIntent(**dict(BASE, quantity=0))
    with pytest.raises(ValidationError):
        ExtractedOrderIntent(**dict(BASE, quantity=10000))
