"""Shared guardrail primitives.

A guardrail check returns a small structured result that is both audited and,
on failure, turned into a natural-language ``REJECTED: ...`` string returned
to the calling agent. Keeping the structure shared means every server audits
guardrail outcomes identically.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GuardrailResult:
    """The outcome of a single named guardrail check."""

    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass
class GuardrailReport:
    """Aggregated results of all guardrail checks for one tool call."""

    results: list[GuardrailResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = "") -> "GuardrailReport":
        self.results.append(GuardrailResult(name=name, passed=passed, detail=detail))
        return self

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[GuardrailResult]:
        return [r for r in self.results if not r.passed]

    def as_audit(self) -> list[dict[str, object]]:
        return [r.to_dict() for r in self.results]

    def rejection_message(self) -> str:
        """Build the natural-language rejection string for failed checks."""
        reasons = "; ".join(f"{r.name}: {r.detail}" for r in self.failures)
        return f"REJECTED: guardrail check failed. {reasons}"
