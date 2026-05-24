"""A2A executor for the order agent (the orchestrator).

Receives a customer order request as an A2A task, runs the LangGraph order
workflow, and returns the resulting :class:`OrderConfirmation` as a JSON
artifact. The graph and its dependencies are built lazily on first use so the
module imports cleanly with no API key or live MCP server.
"""

from __future__ import annotations

import json
import logging
import time

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from order_agent.config import AGENT_NAME
from order_agent.graph import build_order_graph, initial_state, recursion_config
from shared.a2a_utils import enqueue_initial_task, text_part
from shared.audit import emit_audit

logger = logging.getLogger("agentcart.order.executor")

# Name of the artifact the frontend should read for the confirmation JSON.
CONFIRMATION_ARTIFACT = "order-confirmation"


class OrderAgentExecutor(AgentExecutor):
    """Bridge inbound A2A tasks to the order workflow graph."""

    def __init__(self) -> None:
        self._graph = None

    def _ensure_graph(self):
        if self._graph is None:
            # Imported lazily so test code can build the graph with stub deps
            # without ever importing the runtime (which needs the LLM/MCP).
            from order_agent.runtime import build_deps

            self._graph = build_order_graph(build_deps())
        return self._graph

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        started = time.perf_counter()
        task_id = context.task_id or context.context_id or "unknown"
        user_input = context.get_user_input() or ""
        context_id = context.context_id or task_id
        await enqueue_initial_task(
            event_queue, task_id=task_id, context_id=context_id
        )
        updater = TaskUpdater(event_queue, task_id, context_id)
        await updater.start_work()

        state = initial_state(user_input)
        correlation_id = state["correlation_id"]
        status = "ok"
        try:
            graph = self._ensure_graph()
            result = await graph.ainvoke(state, config=recursion_config())
            confirmation = result.get("confirmation") or {}
            await updater.add_artifact(
                [text_part(json.dumps(confirmation))],
                name=CONFIRMATION_ARTIFACT,
            )
            await updater.complete()
        except Exception as exc:  # noqa: BLE001 - surface as task failure
            status = "error"
            logger.exception("order workflow failed")
            await updater.failed(
                updater.new_agent_message(
                    [text_part(f"Order workflow error: {exc}")]
                )
            )
        finally:
            emit_audit(
                task_id=task_id,
                from_agent="frontend",
                to_agent=AGENT_NAME,
                message_summary=user_input,
                status=status,
                duration_ms=(time.perf_counter() - started) * 1000.0,
                correlation_id=correlation_id,
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task_id = context.task_id or context.context_id or "unknown"
        updater = TaskUpdater(event_queue, task_id, context.context_id or task_id)
        await updater.cancel()


def build_executor() -> OrderAgentExecutor:
    """Construct the order agent's A2A executor."""
    return OrderAgentExecutor()
