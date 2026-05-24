"""Final response schema returned by the order agent.

The order agent's terminal A2A artifact carries an :class:`OrderConfirmation`
serialized to JSON. The ``format_response`` workflow node parses the LLM output
through this schema, retries once on failure, and finally falls back to
constructing the confirmation deterministically from workflow state.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

OrderStatus = Literal["confirmed", "failed", "pending_review"]


class OrderConfirmation(BaseModel):
    """The customer-facing result of an order workflow."""

    order_id: str
    status: OrderStatus
    customer_name: str
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0.0)
    total_amount: float = Field(ge=0.0)
    currency: str
    transaction_id: Optional[str] = None
    tracking_id: Optional[str] = None
    estimated_delivery: Optional[str] = None
    failure_reason: Optional[str] = None
    correlation_id: str
