"""Reusable A2A executor for the thin peer agents.

The four peer agents (inventory, payment, shipping, notification) share the
same shape: receive a natural-language task from the Order Agent, run a small
``create_react_agent`` bound to that agent's MCP tools, and return the tool
result text as the A2A artifact. This module factors out that bridge so each
peer's ``executor.py`` is a few lines of configuration.
"""

from __future__ import annotations

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from langchain_core.messages import HumanMessage

from shared.a2a_utils import enqueue_initial_task, text_part
from shared.audit import emit_audit
from shared.correlation import extract_correlation_id
from shared.llm import make_llm
from shared.mcp_client import load_mcp_tools
from shared.tracing import trace_config
import time

logger = logging.getLogger("agentcart.peer")


class PeerAgentExecutor(AgentExecutor):
    """Bridge an inbound A2A task to a LangGraph ReAct agent over MCP tools.

    The ReAct agent is built lazily on first use (so importing the module never
    needs an API key or a live MCP server) and then cached for the process.
    """

    def __init__(
        self,
        *,
        agent_name: str,
        mcp_servers: dict[str, str],
        system_prompt: str,
    ) -> None:
        self._agent_name = agent_name
        self._mcp_servers = mcp_servers
        self._system_prompt = system_prompt
        self._react_agent = None

    async def _ensure_agent(self):
        if self._react_agent is None:
            from langgraph.prebuilt import create_react_agent

            tools = await load_mcp_tools(self._mcp_servers)
            self._react_agent = create_react_agent(
                make_llm(),
                tools,
                prompt=self._system_prompt,
            )
        return self._react_agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        started = time.perf_counter()
        task_id = context.task_id or context.context_id or "unknown"
        user_input = context.get_user_input() or ""
        correlation_id = extract_correlation_id(user_input, default="unknown")

        context_id = context.context_id or task_id
        await enqueue_initial_task(
            event_queue, task_id=task_id, context_id=context_id
        )
        updater = TaskUpdater(event_queue, task_id, context_id)
        await updater.start_work()

        status = "ok"
        try:
            agent = await self._ensure_agent()
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=trace_config(correlation_id, run_name=self._agent_name),
            )
            reply = _last_ai_text(result) or "No result produced."
            await updater.add_artifact(
                [text_part(reply)],
                name=f"{self._agent_name}-result",
            )
            await updater.complete()
        except Exception as exc:  # noqa: BLE001 - surface failure as task state
            status = "error"
            logger.exception("%s failed to handle task", self._agent_name)
            await updater.failed(
                updater.new_agent_message(
                    [text_part(f"{self._agent_name} error: {exc}")]
                )
            )
        finally:
            emit_audit(
                task_id=task_id,
                from_agent="order-agent",
                to_agent=self._agent_name,
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


def _last_ai_text(result: dict) -> str:
    """Extract the final assistant text from a LangGraph result dict."""
    messages = result.get("messages", []) if isinstance(result, dict) else []
    for message in reversed(messages):
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            joined = " ".join(p for p in parts if p).strip()
            if joined:
                return joined
    return ""
