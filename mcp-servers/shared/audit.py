"""Structured JSON audit logging for the MCP layer.

Every tool invocation emits one JSON line to stdout. The schema is identical
across all five servers so that downstream log shippers can parse the whole
MCP layer with a single rule. Sensitive values (payment tokens, etc.) are
redacted before they are written.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

LAYER = "mcp"

# Input keys whose values must never be written verbatim to the audit log.
_SENSITIVE_KEYS = {
    "payment_method_token",
    "paymentMethodToken",
    "token",
}
_REDACTED = "***redacted***"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of ``inputs`` with sensitive values masked."""
    safe: dict[str, Any] = {}
    for key, value in inputs.items():
        if key in _SENSITIVE_KEYS:
            safe[key] = _REDACTED
        else:
            safe[key] = value
    return safe


def emit_audit(
    *,
    tool: str,
    inputs: dict[str, Any],
    guardrail_results: list[dict[str, Any]],
    output_summary: str,
    status: str,
    duration_ms: float,
    correlation_id: str,
) -> None:
    """Write a single structured audit record to stdout as one JSON line."""
    record = {
        "layer": LAYER,
        "timestamp": _utc_now_iso(),
        "tool": tool,
        "inputs": redact_inputs(inputs),
        "guardrail_results": guardrail_results,
        "output_summary": output_summary,
        "status": status,
        "duration_ms": round(duration_ms, 3),
        "correlation_id": correlation_id,
    }
    # Always flush so logs appear promptly under containerized stdout capture.
    sys.stdout.write(json.dumps(record, default=str) + "\n")
    sys.stdout.flush()
