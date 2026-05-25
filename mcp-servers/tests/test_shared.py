"""Tests for the shared infrastructure: rate limiter, audit redaction, runner."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from inventory_mcp.config import settings as inv_settings
from inventory_mcp.server import reserve_stock
from shared.audit import redact_inputs
from shared.guardrails import GuardrailReport
from shared.ratelimit import RateLimiter, RateLimitExceeded
from shared.runner import run_tool


def test_rate_limiter_allows_up_to_limit_then_rejects():
    limiter = RateLimiter(max_calls=3, window_seconds=60)
    for _ in range(3):
        limiter.check("cid")
    with pytest.raises(RateLimitExceeded):
        limiter.check("cid")


def test_rate_limiter_is_per_correlation_id():
    limiter = RateLimiter(max_calls=1, window_seconds=60)
    limiter.check("a")
    # A different correlation id has its own budget.
    limiter.check("b")
    with pytest.raises(RateLimitExceeded):
        limiter.check("a")


def test_rate_limiter_window_eviction(monkeypatch):
    limiter = RateLimiter(max_calls=1, window_seconds=10)
    clock = {"t": 100.0}
    monkeypatch.setattr(limiter, "_now", lambda: clock["t"])
    limiter.check("cid")
    clock["t"] = 111.0  # advance beyond the window
    # Old call evicted, so this is allowed again.
    limiter.check("cid")


def test_audit_redacts_payment_token():
    safe = redact_inputs({"customer_id": "C", "payment_method_token": "tok_secret"})
    assert safe["customer_id"] == "C"
    assert safe["payment_method_token"] == "***redacted***"


async def test_runner_rate_limit_returns_rejection_string_without_rest_call():
    limiter = RateLimiter(max_calls=1, window_seconds=60)

    async def rest_call() -> str:
        return "OK"

    first = await run_tool(
        tool="t",
        correlation_id="cid",
        inputs={},
        guardrails=GuardrailReport(),
        rest_call=rest_call,
        rate_limiter=limiter,
    )
    assert first == "OK"

    second = await run_tool(
        tool="t",
        correlation_id="cid",
        inputs={},
        guardrails=GuardrailReport(),
        rest_call=rest_call,
        rate_limiter=limiter,
    )
    assert second.startswith("REJECTED:")
    assert "rate limit" in second.lower()


async def test_audit_line_emitted_to_stdout(capsys):
    async def rest_call() -> str:
        return "done"

    await run_tool(
        tool="demo_tool",
        correlation_id="cid-audit",
        inputs={"k": "v"},
        guardrails=GuardrailReport().add("g1", True, "ok"),
        rest_call=rest_call,
    )
    out = capsys.readouterr().out
    # Find the audit JSON line (skip any tracing span output).
    audit_lines = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("layer") == "mcp":
            audit_lines.append(obj)
    assert audit_lines, "expected at least one mcp audit line"
    record = audit_lines[-1]
    assert record["tool"] == "demo_tool"
    assert record["correlation_id"] == "cid-audit"
    assert record["status"] == "ok"
    assert "duration_ms" in record
    assert record["guardrail_results"] == [
        {"name": "g1", "passed": True, "detail": "ok"}
    ]


@respx.mock
async def test_tool_call_emits_audit_with_redacted_inputs(capsys):
    respx.post(f"{inv_settings.inventory_service_url}/api/v1/stock/reserve").mock(
        return_value=httpx.Response(
            200,
            json={
                "productId": "AU-001",
                "reservedQty": 1,
                "remainingQty": 9,
                "status": "RESERVED",
            },
        )
    )
    await reserve_stock(product_id="AU-001", quantity=1, correlation_id="cid-x")
    out = capsys.readouterr().out
    assert '"layer": "mcp"' in out
    assert '"tool": "reserve_stock"' in out
