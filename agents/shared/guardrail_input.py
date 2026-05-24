"""Guardrail 1 (input): intent validation and confidence gating.

Runs immediately after the Order Agent extracts a structured intent from the
customer message. It re-checks the structural invariants Pydantic already
enforces, confirms the product and customer resolved to known catalog entries,
and gates the workflow on the model's confidence score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Confidence below this threshold routes the workflow to the clarify path.
CONFIDENCE_THRESHOLD = 0.90


@dataclass
class GuardrailResult:
    """Outcome of a guardrail evaluation."""

    name: str
    passed: bool
    reasons: list[str] = field(default_factory=list)
    needs_clarification: bool = False

    def add(self, ok: bool, message: str) -> None:
        if not ok:
            self.passed = False
            self.reasons.append(message)


def check_input_intent(
    intent: Any,
    *,
    known_product_ids: set[str],
    known_customer_ids: set[str],
    threshold: float = CONFIDENCE_THRESHOLD,
) -> GuardrailResult:
    """Validate an :class:`ExtractedOrderIntent`-shaped object.

    ``intent`` only needs the attributes ``product_id``, ``customer_id``,
    ``quantity``, ``total_amount`` and ``confidence_score`` so the guardrail
    can be unit-tested with a lightweight stand-in.
    """
    result = GuardrailResult(name="input_intent", passed=True)

    if intent.product_id not in known_product_ids:
        result.add(False, f"unknown product_id {intent.product_id!r}")
    if intent.customer_id not in known_customer_ids:
        result.add(False, f"unknown customer_id {intent.customer_id!r}")
    if intent.quantity < 1:
        result.add(False, f"quantity must be >= 1, got {intent.quantity}")
    if intent.total_amount <= 0:
        result.add(False, f"total_amount must be > 0, got {intent.total_amount}")

    confidence = float(intent.confidence_score)
    if confidence < threshold:
        # A low-confidence extraction is not a hard failure: it diverts the
        # workflow to ask the customer to clarify rather than guessing.
        result.needs_clarification = True
        result.reasons.append(
            f"confidence {confidence:.2f} below threshold {threshold:.2f}"
        )

    return result
