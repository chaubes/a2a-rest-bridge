"""Async HTTP client helpers for calling the REST services.

Provides a factory for an ``httpx.AsyncClient`` and small utilities for
parsing the shared REST error contract:

    {timestamp, status, error, message, path, correlationId}

The ``message`` field is surfaced in translated failure strings so the
calling agent receives actionable, human-readable guidance.
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_TIMEOUT_SECONDS = 10.0


def build_client(base_url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> httpx.AsyncClient:
    """Create an async client pinned to a REST service base URL."""
    return httpx.AsyncClient(base_url=base_url, timeout=timeout)


def extract_error_message(response: httpx.Response) -> str:
    """Pull the ``message`` from a REST error-contract body.

    Falls back to the raw response text (truncated) when the body is not the
    expected JSON shape, so we never lose the failure detail entirely.
    """
    try:
        payload: Any = response.json()
    except Exception:
        text = (response.text or "").strip()
        return text[:300] if text else f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and message:
            return message
        error = payload.get("error")
        if isinstance(error, str) and error:
            return error
    return f"HTTP {response.status_code}"


def safe_json(response: httpx.Response) -> dict[str, Any]:
    """Return the JSON body as a dict, or an empty dict on parse failure."""
    try:
        payload = response.json()
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}
