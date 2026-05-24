"""A2A executor integration tests (no network, no LLM, no MCP).

Drives the real a2a-sdk executor stack (RequestContext, EventQueue, TaskUpdater)
with stubbed agent logic, and asserts the events/artifacts produced. Also
covers the correlation-id propagation convention and the peer-call response
extraction helper.
"""

from __future__ import annotations

import json

import pytest
from a2a.auth.user import UnauthenticatedUser
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskArtifactUpdateEvent,
)

from order_agent.executor import CONFIRMATION_ARTIFACT, OrderAgentExecutor
from shared.a2a_utils import extract_response_text, user_message
from shared.correlation import (
    extract_correlation_id,
    format_correlation_token,
    new_correlation_id,
)
from shared.peer_executor import PeerAgentExecutor


class CapturingQueue(EventQueue):
    """An EventQueue that records every enqueued event for assertions."""

    def __init__(self):
        self.events: list = []

    async def enqueue_event(self, event) -> None:
        self.events.append(event)


def make_context(text: str) -> RequestContext:
    request = SendMessageRequest(message=user_message(text))
    call_context = ServerCallContext(user=UnauthenticatedUser())
    return RequestContext(
        call_context=call_context,
        request=request,
        task_id="task-1",
        context_id="ctx-1",
    )


def artifact_text(events: list) -> str:
    """Concatenate text from every artifact-update event in the stream."""
    chunks: list[str] = []
    for event in events:
        if isinstance(event, TaskArtifactUpdateEvent):
            for part in event.artifact.parts:
                if part.text:
                    chunks.append(part.text)
    return "\n".join(chunks)


# --------------------------------------------------------------------------- #
# Correlation-id convention
# --------------------------------------------------------------------------- #


def test_correlation_id_round_trips_through_task_text():
    cid = new_correlation_id()
    assert cid.startswith("ord-")
    text = f"Reserve 2 units of WB-001. {format_correlation_token(cid)}"
    assert extract_correlation_id(text) == cid


def test_correlation_id_default_when_absent():
    assert extract_correlation_id("no token here", default="fallback") == "fallback"


# --------------------------------------------------------------------------- #
# Peer executor
# --------------------------------------------------------------------------- #


class _StubReactAgent:
    """Mimics a compiled LangGraph agent: returns a final AI message."""

    def __init__(self, reply: str):
        self._reply = reply

    async def ainvoke(self, _inputs):
        from langchain_core.messages import AIMessage

        return {"messages": [AIMessage(content=self._reply)]}


@pytest.mark.asyncio
async def test_peer_executor_emits_artifact_with_tool_result():
    executor = PeerAgentExecutor(
        agent_name="inventory-agent",
        mcp_servers={"inventory": "http://unused"},
        system_prompt="stub",
    )
    # Inject a stub react agent so no LLM/MCP is required.
    executor._react_agent = _StubReactAgent(
        "Reserved 2 units of WB-001. Reservation successful."
    )

    queue = CapturingQueue()
    ctx = make_context(
        f"Reserve 2 units of WB-001. {format_correlation_token('ord-abcd1234')}"
    )
    await executor.execute(ctx, queue)

    text = artifact_text(queue.events)
    assert "Reserved 2 units of WB-001" in text


@pytest.mark.asyncio
async def test_peer_executor_marks_task_failed_on_error():
    class _Boom:
        async def ainvoke(self, _inputs):
            raise RuntimeError("mcp down")

    executor = PeerAgentExecutor(
        agent_name="payment-agent",
        mcp_servers={"payment": "http://unused"},
        system_prompt="stub",
    )
    executor._react_agent = _Boom()

    queue = CapturingQueue()
    await executor.execute(make_context("charge it, correlation_id=ord-1"), queue)

    # The stream must contain a FAILED status update and no result artifact.
    from a2a.types import TaskState, TaskStatusUpdateEvent

    statuses = [e for e in queue.events if isinstance(e, TaskStatusUpdateEvent)]
    assert any(
        s.status.state == TaskState.TASK_STATE_FAILED for s in statuses
    )
    assert not any(
        isinstance(e, TaskArtifactUpdateEvent) for e in queue.events
    )


# --------------------------------------------------------------------------- #
# Order executor
# --------------------------------------------------------------------------- #


class _StubGraph:
    """Mimics a compiled order graph: returns a fixed confirmation."""

    def __init__(self, confirmation: dict):
        self._confirmation = confirmation

    async def ainvoke(self, _state, config=None):
        return {"confirmation": self._confirmation, "status": self._confirmation["status"]}


@pytest.mark.asyncio
async def test_order_executor_returns_confirmation_json_artifact():
    confirmation = {
        "order_id": "ORD-42",
        "status": "confirmed",
        "customer_name": "Alice Johnson",
        "product_name": "Blue Widget",
        "quantity": 2,
        "unit_price": 14.99,
        "total_amount": 29.98,
        "currency": "AUD",
        "transaction_id": "txn-abc123",
        "tracking_id": "trk-xyz789",
        "estimated_delivery": None,
        "failure_reason": None,
        "correlation_id": "ord-deadbeef",
    }
    executor = OrderAgentExecutor()
    executor._graph = _StubGraph(confirmation)

    queue = CapturingQueue()
    await executor.execute(make_context("Order 2 Blue Widgets for Alice."), queue)

    # The confirmation artifact must carry the OrderConfirmation as JSON.
    artifact_events = [
        e for e in queue.events if isinstance(e, TaskArtifactUpdateEvent)
    ]
    assert artifact_events, "expected an artifact update event"
    assert artifact_events[0].artifact.name == CONFIRMATION_ARTIFACT
    parsed = json.loads(artifact_text(queue.events))
    assert parsed["order_id"] == "ORD-42"
    assert parsed["status"] == "confirmed"
    assert parsed["total_amount"] == pytest.approx(29.98)


# --------------------------------------------------------------------------- #
# Response extraction helper
# --------------------------------------------------------------------------- #


def test_extract_response_text_prefers_artifacts():
    task = Task(id="t", context_id="c")
    artifact = Artifact(artifact_id="a", name="r", parts=[Part(text="hello")])
    task.artifacts.append(artifact)
    assert extract_response_text(task) == "hello"
