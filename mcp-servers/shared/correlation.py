"""Correlation-id helpers.

A single correlation id threads a customer action across all three layers
(agent -> MCP tool -> REST service). These helpers keep the header and body
field names consistent everywhere they are forwarded.
"""

from __future__ import annotations

import uuid

CORRELATION_HEADER = "X-Correlation-ID"
CORRELATION_BODY_FIELD = "correlationId"


def new_correlation_id() -> str:
    """Generate a fresh correlation id.

    Useful for local smoke tests; in normal operation the id is supplied by
    the calling agent and forwarded unchanged.
    """
    return str(uuid.uuid4())


def correlation_headers(correlation_id: str) -> dict[str, str]:
    """Build the HTTP headers that carry the correlation id downstream."""
    return {CORRELATION_HEADER: correlation_id}


def with_correlation(body: dict, correlation_id: str) -> dict:
    """Return a copy of ``body`` with the camelCase correlation field set."""
    enriched = dict(body)
    enriched[CORRELATION_BODY_FIELD] = correlation_id
    return enriched
