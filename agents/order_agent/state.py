"""Workflow state carried through the order agent's StateGraph."""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class OrderState(TypedDict, total=False):
    """Mutable state threaded across the order workflow nodes.

    ``total=False`` so nodes may populate keys incrementally; every node reads
    only the keys it needs and writes a partial update.
    """

    # Inputs and identifiers
    customer_message: str
    correlation_id: str
    executed_steps: list[str]

    # Extracted intent (as a plain dict so the state stays serializable)
    intent: Optional[dict[str, Any]]
    confidence_score: float
    needs_clarification: bool

    # Resolved facts
    customer_name: str
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    currency: str
    address: dict[str, Any]
    estimated_delivery: Optional[str]

    # Step outcomes (natural-language replies from peers / MCP)
    inventory_result: str
    inventory_ok: bool
    payment_result: str
    payment_ok: bool
    transaction_id: Optional[str]
    shipping_result: str
    tracking_id: Optional[str]
    order_id: Optional[str]
    save_result: str
    notification_result: str

    # Control + terminal
    status: str
    failure_reason: Optional[str]
    confirmation: dict[str, Any]
