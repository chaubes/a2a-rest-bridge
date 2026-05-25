"""Unit tests for the per-server guardrail checks."""

from __future__ import annotations

import pytest

from inventory_mcp import guardrails as inv
from notification_mcp import guardrails as notif
from order_mcp import guardrails as order
from payment_mcp import guardrails as pay
from shipping_mcp import guardrails as ship


# --- inventory ---------------------------------------------------------------

@pytest.mark.parametrize("product_id", ["AU-001", "ZZ-999", "DE-042"])
def test_inventory_valid_product_id_passes(product_id):
    report = inv.check_product_and_quantity(product_id, 5)
    assert report.passed


@pytest.mark.parametrize(
    "product_id",
    ["au-001", "A-001", "AUS-001", "AU-1", "AU-0001", "AU001", "", "AU-01A"],
)
def test_inventory_invalid_product_id_rejected(product_id):
    report = inv.check_product_and_quantity(product_id, 5)
    assert not report.passed
    assert any(f.name == "product_id_format" for f in report.failures)


@pytest.mark.parametrize("quantity", [0, -1, 10000, 99999])
def test_inventory_quantity_out_of_range_rejected(quantity):
    report = inv.check_product_and_quantity("AU-001", quantity)
    assert not report.passed
    assert any(f.name == "quantity_range" for f in report.failures)


@pytest.mark.parametrize("quantity", [1, 5000, 9999])
def test_inventory_quantity_in_range_passes(quantity):
    report = inv.check_product_and_quantity("AU-001", quantity)
    assert report.passed


def test_inventory_bool_quantity_rejected():
    # bool is a subclass of int and must not slip through.
    report = inv.check_product_and_quantity("AU-001", True)
    assert not report.passed


# --- payment -----------------------------------------------------------------

@pytest.mark.parametrize("amount", [0.01, 100, 50000])
def test_payment_amount_within_ceiling_passes(amount):
    report = pay.check_charge(amount, "AUD")
    assert report.passed


@pytest.mark.parametrize("amount", [0, -5])
def test_payment_amount_non_positive_rejected(amount):
    report = pay.check_charge(amount, "AUD")
    assert not report.passed


def test_payment_amount_over_ceiling_rejected_with_human_approval_message():
    report = pay.check_charge(50000.01, "AUD")
    assert not report.passed
    failure = next(f for f in report.failures if f.name == "amount_ceiling")
    assert "human approval" in failure.detail.lower()
    assert "50000" in failure.detail


@pytest.mark.parametrize("currency", ["AUD", "USD", "EUR", "GBP"])
def test_payment_valid_currency_passes(currency):
    report = pay.check_charge(10, currency)
    assert report.passed


@pytest.mark.parametrize("currency", ["JPY", "aud", "", "BTC"])
def test_payment_bad_currency_rejected(currency):
    report = pay.check_charge(10, currency)
    assert not report.passed
    assert any(f.name == "currency_allowed" for f in report.failures)


# --- shipping ----------------------------------------------------------------

@pytest.mark.parametrize("country", ["AU", "US", "UK", "DE"])
def test_shipping_valid_country_passes(country):
    report = ship.check_create_shipment(
        "ORD-1", "1 Smith St", "Sydney", "NSW", "2000", country
    )
    assert report.passed


@pytest.mark.parametrize("country", ["FR", "au", "", "USA"])
def test_shipping_bad_country_rejected(country):
    report = ship.check_create_shipment(
        "ORD-1", "1 Smith St", "Sydney", "NSW", "2000", country
    )
    assert not report.passed
    assert any(f.name == "country_allowed" for f in report.failures)


def test_shipping_empty_address_field_rejected():
    report = ship.check_create_shipment("ORD-1", "  ", "Sydney", "NSW", "2000", "AU")
    assert not report.passed
    assert any(f.name == "address_line1_present" for f in report.failures)


# --- order -------------------------------------------------------------------

def test_order_valid_passes():
    report = order.check_create_order(
        "CUST-1", "AU-001", 2, 199.5, "AUD", "TX-1", "TRK-1"
    )
    assert report.passed


def test_order_zero_total_amount_rejected():
    report = order.check_create_order(
        "CUST-1", "AU-001", 2, 0, "AUD", "TX-1", "TRK-1"
    )
    assert not report.passed
    assert any(f.name == "total_amount_positive" for f in report.failures)


def test_order_missing_field_rejected():
    report = order.check_create_order("", "AU-001", 2, 10, "AUD", "TX-1", "TRK-1")
    assert not report.passed
    assert any(f.name == "customer_id_present" for f in report.failures)


# --- notification ------------------------------------------------------------

@pytest.mark.parametrize("channel", ["email", "sms"])
def test_notification_valid_channel_passes(channel):
    report = notif.check_send_notification("hello", channel)
    assert report.passed


@pytest.mark.parametrize("channel", ["push", "EMAIL", "", "fax"])
def test_notification_bad_channel_rejected(channel):
    report = notif.check_send_notification("hello", channel)
    assert not report.passed
    assert any(f.name == "channel_allowed" for f in report.failures)


def test_notification_oversized_message_rejected():
    report = notif.check_send_notification("x" * 1001, "email")
    assert not report.passed
    assert any(f.name == "message_length" for f in report.failures)


def test_notification_max_length_message_passes():
    report = notif.check_send_notification("x" * 1000, "email")
    assert report.passed
