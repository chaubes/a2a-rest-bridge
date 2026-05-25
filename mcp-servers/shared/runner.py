"""Tool execution scaffolding shared by every MCP server.

``run_tool`` standardizes the lifecycle of a tool call:

  1. rate-limit the correlation id,
  2. run guardrail checks BEFORE any REST call,
  3. on rejection, return the natural-language ``REJECTED: ...`` string,
  4. otherwise invoke the supplied REST coroutine,
  5. audit the outcome (status, duration, summary) as structured JSON.

The REST coroutine returns the natural-language string the agent will read.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from shared.audit import emit_audit
from shared.guardrails import GuardrailReport
from shared.ratelimit import RateLimitExceeded, shared_rate_limiter

# Length cap for the audited output summary so logs stay compact.
_SUMMARY_MAX = 240


def _summarize(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _SUMMARY_MAX else text[: _SUMMARY_MAX - 1] + "…"


async def run_tool(
    *,
    tool: str,
    correlation_id: str,
    inputs: dict[str, Any],
    guardrails: GuardrailReport,
    rest_call: Callable[[], Awaitable[str]],
    rate_limiter=shared_rate_limiter,
) -> str:
    """Execute one tool call with rate limiting, guardrails, and auditing."""
    start = time.perf_counter()

    # --- Rate limit (before anything else) ---
    try:
        rate_limiter.check(correlation_id)
    except RateLimitExceeded as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        message = (
            f"REJECTED: rate limit exceeded for this correlation id "
            f"({exc.max_calls} calls per {int(exc.window_seconds)}s). "
            "Do NOT retry immediately; back off and reuse status checks "
            "instead of re-issuing the same call."
        )
        emit_audit(
            tool=tool,
            inputs=inputs,
            guardrail_results=guardrails.as_audit(),
            output_summary=_summarize(message),
            status="rate_limited",
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )
        return message

    # --- Guardrails (before any REST call) ---
    if not guardrails.passed:
        message = guardrails.rejection_message()
        duration_ms = (time.perf_counter() - start) * 1000.0
        emit_audit(
            tool=tool,
            inputs=inputs,
            guardrail_results=guardrails.as_audit(),
            output_summary=_summarize(message),
            status="rejected",
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )
        return message

    # --- REST call ---
    try:
        result = await rest_call()
        status = "ok"
    except Exception as exc:  # noqa: BLE001 - surfaced to the agent as text.
        result = (
            f"FAILED: the {tool} request could not be completed due to an "
            f"unexpected error contacting the service: {exc}. "
            "Do NOT retry without checking the service status first."
        )
        status = "error"

    duration_ms = (time.perf_counter() - start) * 1000.0
    emit_audit(
        tool=tool,
        inputs=inputs,
        guardrail_results=guardrails.as_audit(),
        output_summary=_summarize(result),
        status=status,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
    )
    return result
