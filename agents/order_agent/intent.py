"""Structured order-intent schema extracted from the customer message.

The :class:`ExtractedOrderIntent` model is the contract between the intent
extraction step and the rest of the workflow. Two validators enforce business
invariants the LLM cannot be trusted to get right: the total amount is always
recomputed from ``unit_price * quantity``, and any supplied delivery date must
be in the future.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ExtractedOrderIntent(BaseModel):
    """A normalized purchase intent resolved against the catalog/profiles."""

    product_id: str
    product_name: str
    quantity: int = Field(ge=1, le=9999)
    unit_price: float = Field(ge=0.01)
    total_amount: float = Field(ge=0.01)
    delivery_date: Optional[str] = None
    shipping_method: str = "standard"
    customer_id: str
    address: dict = Field(default_factory=dict)
    confidence_score: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _override_total_amount(self) -> "ExtractedOrderIntent":
        """Force ``total_amount`` to the deterministic catalog computation.

        The LLM frequently mis-multiplies; the authoritative total is always
        ``round(unit_price * quantity, 2)``. We override silently whenever the
        supplied value differs by more than one cent.
        """
        expected = round(self.unit_price * self.quantity, 2)
        if abs(self.total_amount - expected) > 0.01:
            object.__setattr__(self, "total_amount", expected)
        return self

    @model_validator(mode="after")
    def _delivery_date_must_be_future(self) -> "ExtractedOrderIntent":
        """Reject a delivery date that is not strictly in the future."""
        if self.delivery_date is None:
            return self
        try:
            parsed = datetime.fromisoformat(self.delivery_date).date()
        except ValueError as exc:
            raise ValueError(
                f"delivery_date {self.delivery_date!r} is not an ISO date"
            ) from exc
        if parsed <= date.today():
            raise ValueError(
                f"delivery_date {self.delivery_date!r} must be in the future"
            )
        return self
