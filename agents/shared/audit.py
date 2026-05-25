"""Structured JSON audit logging for the A2A layer.

Every A2A task (an agent receiving work, or an agent calling a peer) emits one
JSON line to stdout. The schema is identical across all five agents so a log
shipper can parse the whole layer with a single rule. Sensitive values such as
payment tokens are redacted from the message summary before it is written.
"""

from __future__ import annotations

import json
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

LAYER = "a2a"

# Patterns whose values must never be written verbatim to the audit log.
_SENSITIVE_PATTERNS = [
    re.compile(r"(payment_method_token\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(token\s*=\s*)(\S+)", re.IGNORECASE),
]
_REDACTED = "***redacted***"
_SUMMARY_MAX = 280


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize(text: str) -> str:
    """Redact secrets and truncate a message to a short, log-safe summary."""
    if not text:
        return ""
    redacted = text
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(rf"\1{_REDACTED}", redacted)
    redacted = " ".join(redacted.split())
    if len(redacted) > _SUMMARY_MAX:
        redacted = redacted[: _SUMMARY_MAX - 1] + "…"
    return redacted


def emit_audit(
    *,
    task_id: str,
    from_agent: str,
    to_agent: str,
    message_summary: str,
    status: str,
    duration_ms: float,
    correlation_id: str,
) -> None:
    """Write a single structured A2A audit record to stdout as one JSON line."""
    record = {
        "layer": LAYER,
        "timestamp": _utc_now_iso(),
        "task_id": task_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_summary": summarize(message_summary),
        "status": status,
        "duration_ms": round(duration_ms, 3),
        "correlation_id": correlation_id,
    }
    sys.stdout.write(json.dumps(record, default=str) + "\n")
    sys.stdout.flush()


@contextmanager
def audit_task(
    *,
    task_id: str,
    from_agent: str,
    to_agent: str,
    message_summary: str,
    correlation_id: str,
) -> Iterator[dict]:
    """Time an A2A task and emit one audit record when the block exits.

    Yields a small mutable dict; set ``result["status"]`` inside the block to
    override the recorded status (defaults to ``ok`` / ``error``).
    """
    start = time.perf_counter()
    result: dict = {"status": None}
    try:
        yield result
    except Exception:
        duration = (time.perf_counter() - start) * 1000.0
        emit_audit(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_summary=message_summary,
            status="error",
            duration_ms=duration,
            correlation_id=correlation_id,
        )
        raise
    duration = (time.perf_counter() - start) * 1000.0
    emit_audit(
        task_id=task_id,
        from_agent=from_agent,
        to_agent=to_agent,
        message_summary=message_summary,
        status=result["status"] or "ok",
        duration_ms=duration,
        correlation_id=correlation_id,
    )
