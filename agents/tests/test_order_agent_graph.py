"""Tests for the order workflow StateGraph with mocked peers, MCP, and LLM.

No network, no real LLM, no MCP server: the LLM is a FakeListChatModel that
returns canned JSON, and the peer A2A client / order-save callable are stubs
that record their calls.
"""

from __future__ import annotations

import json

import pytest
from langchain_core.language_models import FakeListChatModel

from order_agent.graph import (
    OrderGraphDeps,
    build_audit_steps,
    build_order_graph,
    initial_state,
    recursion_config,
)


def test_build_audit_steps_produces_three_layer_chain():
    """A completed-order state yields ordered, layer-tagged audit steps."""
    state = {
        "quantity": 3,
        "product_name": "Blue Widget",
        "customer_name": "Alice Johnson",
        "total_amount": 44.97,
        "currency": "AUD",
        "executed_steps": [
            "check_inventory",
            "process_payment",
            "arrange_shipping",
            "save_order",
            "send_notification",
        ],
        "inventory_result": "Reserved 3 units of WB-001.",
        "payment_result": "Payment successful. Transaction ID: txn-1234.",
        "shipping_result": "Shipment created. Tracking ID: trk-5678.",
        "save_result": "Order ord-9999 saved.",
        "notification_result": "Notification sent to C-001 via email.",
    }

    steps = build_audit_steps(state)

    layers = [s["layer"] for s in steps]
    # Intent (agent) first, an A2A delegation + REST result per peer step, and
    # an MCP entry for the order-save step.
    assert layers[0] == "agent"
    assert "a2a" in layers and "rest" in layers and "mcp" in layers
    # Every step carries a non-empty summary.
    assert all(s["summary"] for s in steps)
    # The payment REST result is surfaced verbatim for the audit panel.
    assert any("Transaction ID: txn-1234" in s["summary"] for s in steps)


def test_build_audit_steps_empty_when_nothing_ran():
    assert build_audit_steps({"executed_steps": []}) == []

EXTRACTION_JSON = json.dumps(
    {
        "product_id": "WB-001",
        "product_name": "Blue Widget",
        "quantity": 2,
        "unit_price": 14.99,
        "total_amount": 29.98,
        "delivery_date": None,
        "shipping_method": "standard",
        "customer_id": "C-001",
        "address": {
            "line1": "Level 12, 100 George St",
            "city": "Sydney",
            "state": "NSW",
            "postcode": "2000",
            "country": "AU",
        },
        "confidence_score": 0.97,
    }
)

# The format_response node also calls the LLM; give it a valid confirmation.
RESPONSE_JSON = json.dumps(
    {
        "order_id": "ORD-42",
        "status": "confirmed",
        "customer_name": "Alice Johnson",
        "product_name": "Blue Widget",
        "quantity": 2,
        "unit_price": 14.99,
        "total_amount": 29.98,
        "currency": "AUD",
        "transaction_id": "txn-abc123",
        "tracking_id": "trk-xyz789",
        "estimated_delivery": None,
        "failure_reason": None,
        "correlation_id": "ord-placeholder",
    }
)

LOW_CONFIDENCE_JSON = json.dumps(
    {
        "product_id": "WB-001",
        "product_name": "Blue Widget",
        "quantity": 1,
        "unit_price": 14.99,
        "total_amount": 14.99,
        "shipping_method": "standard",
        "customer_id": "C-001",
        "address": {},
        "confidence_score": 0.40,
    }
)


class RecordingPeer:
    """Stub A2A peer caller with scripted replies per peer name."""

    def __init__(self, replies: dict[str, str]):
        self.replies = replies
        self.calls: list[tuple[str, str]] = []

    async def __call__(self, peer_name: str, message_text: str) -> str:
        self.calls.append((peer_name, message_text))
        return self.replies[peer_name]

    def peers_called(self) -> list[str]:
        return [name for name, _ in self.calls]


class RecordingSaver:
    def __init__(self, reply: str = "Saved order ORD-42."):
        self.reply = reply
        self.calls: list[dict] = []

    async def __call__(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.reply


def make_llm(*responses: str) -> FakeListChatModel:
    return FakeListChatModel(responses=list(responses))


@pytest.mark.asyncio
async def test_happy_path_completes_confirmed():
    peer = RecordingPeer(
        {
            "inventory": "Reserved 2 units of WB-001. Reservation successful.",
            "payment": "Charged customer C-001. Transaction txn-abc123 approved.",
            "shipping": "Shipment created. Tracking id trk-xyz789.",
            "notification": "Notification sent to C-001 via email.",
        }
    )
    saver = RecordingSaver("Order saved with id ORD-42.")
    deps = OrderGraphDeps(
        llm=make_llm(EXTRACTION_JSON, RESPONSE_JSON),
        call_peer=peer,
        save_order=saver,
    )
    graph = build_order_graph(deps)

    result = await graph.ainvoke(
        initial_state("Order 2 Blue Widgets for Alice Johnson."),
        config=recursion_config(),
    )

    conf = result["confirmation"]
    assert conf["status"] == "confirmed"
    assert conf["total_amount"] == pytest.approx(29.98)  # catalog-derived
    assert conf["transaction_id"] == "txn-abc123"
    assert conf["tracking_id"] == "trk-xyz789"
    # correlation id is overridden from workflow state, not the LLM placeholder
    assert conf["correlation_id"].startswith("ord-")
    assert conf["correlation_id"] != "ord-placeholder"
    # All four peers were engaged, save was called, and no token leaked.
    assert peer.peers_called() == [
        "inventory",
        "payment",
        "shipping",
        "notification",
    ]
    assert len(saver.calls) == 1
    assert "payment_method_token" not in json.dumps(conf)


@pytest.mark.asyncio
async def test_payment_declined_triggers_rollback_and_failure():
    peer = RecordingPeer(
        {
            "inventory": "Reserved 2 units of WB-001. Reservation successful.",
            "payment": "Payment declined: insufficient funds.",
            "shipping": "Shipment created. Tracking id trk-xyz789.",
            "notification": "Notification sent.",
        }
    )
    saver = RecordingSaver()
    deps = OrderGraphDeps(
        llm=make_llm(EXTRACTION_JSON, RESPONSE_JSON),
        call_peer=peer,
        save_order=saver,
    )
    graph = build_order_graph(deps)

    result = await graph.ainvoke(
        initial_state("Order 2 Blue Widgets for Alice Johnson."),
        config=recursion_config(),
    )

    # Inventory called twice (reserve, then release on rollback); payment once.
    called = peer.peers_called()
    assert called == ["inventory", "payment", "inventory"]
    # Shipping, save, and notification must NOT run on a payment failure.
    assert "shipping" not in called
    assert "notification" not in called
    assert saver.calls == []

    conf = result["confirmation"]
    assert conf["status"] == "failed"
    assert "declined" in (conf["failure_reason"] or "").lower()
    assert "rollback_inventory" in result["executed_steps"]


@pytest.mark.asyncio
async def test_stock_unavailable_skips_payment():
    peer = RecordingPeer(
        {
            "inventory": "FAILED: stock unavailable for WB-001.",
            "payment": "should not be called",
            "shipping": "should not be called",
            "notification": "should not be called",
        }
    )
    saver = RecordingSaver()
    deps = OrderGraphDeps(
        llm=make_llm(EXTRACTION_JSON, RESPONSE_JSON),
        call_peer=peer,
        save_order=saver,
    )
    graph = build_order_graph(deps)

    result = await graph.ainvoke(
        initial_state("Order 2 Blue Widgets for Alice Johnson."),
        config=recursion_config(),
    )

    assert peer.peers_called() == ["inventory"]
    assert saver.calls == []
    assert result["confirmation"]["status"] == "failed"


@pytest.mark.asyncio
async def test_low_confidence_routes_to_clarify():
    peer = RecordingPeer({"inventory": "", "payment": "", "shipping": "", "notification": ""})
    saver = RecordingSaver()
    deps = OrderGraphDeps(
        llm=make_llm(LOW_CONFIDENCE_JSON, RESPONSE_JSON),
        call_peer=peer,
        save_order=saver,
    )
    graph = build_order_graph(deps)

    result = await graph.ainvoke(
        initial_state("um maybe a widget?"),
        config=recursion_config(),
    )

    # No side effects run on the clarify path.
    assert peer.calls == []
    assert saver.calls == []
    assert result["confirmation"]["status"] == "pending_review"
