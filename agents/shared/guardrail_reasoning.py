"""Guardrail 2 (reasoning): plan sanity and recursion limiting.

Sits between the orchestration steps to ensure the workflow never executes an
unsafe ordering of actions (for example charging a customer before stock has
been reserved, or shipping before payment has cleared) and to bound the number
of graph hops via the configured recursion limit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# The canonical, safe ordering of the side-effecting workflow steps.
SAFE_PLAN_ORDER = [
    "check_inventory",
    "process_payment",
    "arrange_shipping",
    "save_order",
    "send_notification",
]


@dataclass
class ReasoningResult:
    """Outcome of a reasoning-plan evaluation."""

    passed: bool = True
    reasons: list[str] = field(default_factory=list)

    def violate(self, message: str) -> None:
        self.passed = False
        self.reasons.append(message)


def max_recursion_limit() -> int:
    """Read the configured LangGraph recursion limit (default 15)."""
    raw = os.getenv("AGENT_MAX_RECURSION_LIMIT", "15")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 15
    return value if value > 0 else 15


def check_plan(executed_steps: list[str]) -> ReasoningResult:
    """Validate the order in which side-effecting steps were executed.

    Rules enforced:
      * payment must never precede a successful inventory reservation;
      * shipping must never precede payment;
      * the same side-effecting step must not run twice.
    """
    result = ReasoningResult()
    seen: set[str] = set()

    for step in executed_steps:
        if step in seen and step in SAFE_PLAN_ORDER:
            result.violate(f"step {step!r} executed more than once")
        seen.add(step)

    if "process_payment" in executed_steps:
        if "check_inventory" not in executed_steps:
            result.violate("payment attempted before inventory was checked")
        elif executed_steps.index("process_payment") < executed_steps.index(
            "check_inventory"
        ):
            result.violate("payment attempted before inventory was checked")

    if "arrange_shipping" in executed_steps:
        if "process_payment" not in executed_steps:
            result.violate("shipping arranged before payment was processed")
        elif executed_steps.index("arrange_shipping") < executed_steps.index(
            "process_payment"
        ):
            result.violate("shipping arranged before payment was processed")

    return result


def within_recursion_budget(hops: int) -> bool:
    """Return True while the workflow stays within the recursion budget."""
    return hops <= max_recursion_limit()
