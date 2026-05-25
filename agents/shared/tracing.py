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


def trace_config(correlation_id: str, run_name: str) -> dict:
    """Build a LangGraph/LangChain ``RunnableConfig`` that groups traces.

    Tagging every run with the ``correlation_id`` (as both a metadata field and
    a LangSmith thread key) means a single order's runs across all five agents
    can be filtered by ``metadata.correlation_id`` and collapsed into one
    thread in the LangSmith UI. ``thread_id`` is the key LangSmith uses for its
    Threads view, so the whole order shows up as one grouped conversation.
    """
    return {
        "run_name": f"{run_name} [{correlation_id}]",
        "metadata": {
            "correlation_id": correlation_id,
            "thread_id": correlation_id,
        },
        "tags": [f"correlation:{correlation_id}"],
    }
