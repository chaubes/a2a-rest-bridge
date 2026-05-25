"""Correlation-id generation and propagation helpers.

A single correlation id threads a customer action across all three layers
(A2A agent -> MCP tool -> REST service). The Order Agent mints one id at the
start of a workflow and forwards it unchanged on every A2A task and MCP call.
Peer agents extract the id from the inbound task text so the same id reaches
the MCP layer.
"""

from __future__ import annotations

import re
import secrets

CORRELATION_HEADER = "X-Correlation-ID"

# Order Agent embeds the id in task text as ``correlation_id=<id>`` so peer
# agents (which receive natural language) can recover it deterministically.
_CORRELATION_TOKEN = re.compile(r"correlation_id\s*=\s*([A-Za-z0-9\-]+)")


def new_correlation_id() -> str:
    """Mint a fresh workflow correlation id of the form ``ord-<8hex>``."""
    return f"ord-{secrets.token_hex(4)}"


def format_correlation_token(correlation_id: str) -> str:
    """Render the inline token the Order Agent appends to peer task text."""
    return f"correlation_id={correlation_id}"


def extract_correlation_id(text: str, default: str | None = None) -> str | None:
    """Recover the correlation id from a task message, if present.

    Returns ``default`` when no ``correlation_id=<id>`` token is found.
    """
    if not text:
        return default
    match = _CORRELATION_TOKEN.search(text)
    if match:
        return match.group(1)
    return default
