"""LangSmith tracing configuration.

LangGraph and LangChain auto-instrument when the LangSmith environment
variables are present, so this helper simply validates that the required
variables are set and emits a clear warning otherwise. It is safe to call at
process start regardless of whether tracing is enabled.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("agentcart.tracing")


def configure_langsmith() -> bool:
    """Enable LangSmith tracing when configured via the environment.

    Returns ``True`` when ``LANGSMITH_TRACING=true`` and ``LANGSMITH_API_KEY``
    are both set (LangGraph then auto-instruments via these env vars), and
    ``False`` otherwise. Never raises.
    """
    enabled = os.getenv("LANGSMITH_TRACING", "false").strip().lower() == "true"
    if not enabled:
        logger.info("LangSmith tracing disabled (LANGSMITH_TRACING != 'true').")
        return False

    if not os.getenv("LANGSMITH_API_KEY"):
        logger.warning(
            "LANGSMITH_TRACING=true but LANGSMITH_API_KEY is unset; "
            "tracing will not be active."
        )
        return False

    # LangChain reads LANGCHAIN_TRACING_V2/LANGSMITH_TRACING directly; mirror
    # the flag onto the name LangChain looks for so either spelling works.
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    project = os.getenv("LANGSMITH_PROJECT", "agentcart")
    logger.info("LangSmith tracing enabled for project %r.", project)
    return True
