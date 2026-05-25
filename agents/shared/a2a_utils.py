"""A2A server/client glue for a2a-sdk 1.x.

In a2a-sdk 1.x the high-level ``A2AStarletteApplication`` of the 0.x line is
gone; a server is assembled from route builders (``create_jsonrpc_routes`` and
``create_agent_card_routes``) mounted on a Starlette app, and clients are built
with ``create_client`` / ``ClientFactory``. These helpers wrap those building
blocks so every agent server and every peer call is constructed the same way.

The A2A spec moved the well-known card path to ``/.well-known/agent-card.json``;
we serve the card at both that path and the legacy ``/.well-known/agent.json``
so older clients (and the project's frontend) can resolve either one.
"""

from __future__ import annotations

import logging
import os
from typing import Iterable

import httpx
from a2a.client import ClientConfig, create_client
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.routes.agent_card_routes import agent_card_to_dict
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.events import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatus,
)
from a2a.utils import TransportProtocol
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH, DEFAULT_RPC_URL
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger("agentcart.a2a")

# Legacy well-known path used by the 0.x line and many existing clients.
LEGACY_AGENT_CARD_PATH = "/.well-known/agent.json"


def build_agent_card(
    *,
    name: str,
    description: str,
    url: str,
    version: str,
    skills: Iterable[AgentSkill],
    streaming: bool = False,
) -> AgentCard:
    """Construct an AgentCard advertising a single JSON-RPC HTTP interface.

    The JSON-RPC endpoint is mounted at the app root (``DEFAULT_RPC_URL`` is
    ``/``), so ``url`` is simply the agent's base URL.
    """
    return AgentCard(
        name=name,
        description=description,
        version=version,
        supported_interfaces=[
            AgentInterface(protocol_binding=TransportProtocol.JSONRPC, url=url),
        ],
        capabilities=AgentCapabilities(streaming=streaming),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain", "application/json"],
        skills=list(skills),
    )


def build_app(
    *,
    agent_card: AgentCard,
    executor: AgentExecutor,
    cors_origins: list[str] | None = None,
) -> Starlette:
    """Assemble the Starlette app that serves an agent over A2A JSON-RPC.

    Mounts the JSON-RPC endpoint at :data:`DEFAULT_RPC_URL` and serves the
    agent card at both the current and legacy well-known paths. When
    ``cors_origins`` is supplied, a permissive :class:`CORSMiddleware` is added
    so a browser frontend can call the agent directly.
    """
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    routes: list[Route] = []
    # Enable v0.3 backward compatibility on the same endpoint so clients that
    # do not send an ``A2A-Version`` header (interpreted as v0.3) and clients
    # that send v1.0 are both served on a single port.
    routes.extend(
        create_jsonrpc_routes(handler, DEFAULT_RPC_URL, enable_v0_3_compat=True)
    )
    routes.extend(
        create_agent_card_routes(agent_card, card_url=AGENT_CARD_WELL_KNOWN_PATH)
    )

    async def _legacy_card(_request: Request) -> JSONResponse:
        return JSONResponse(agent_card_to_dict(agent_card))

    routes.append(Route(LEGACY_AGENT_CARD_PATH, _legacy_card, methods=["GET"]))

    middleware = None
    if cors_origins is not None:
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ]

    return Starlette(routes=routes, middleware=middleware)


async def enqueue_initial_task(
    event_queue: EventQueue,
    *,
    task_id: str,
    context_id: str,
) -> None:
    """Enqueue the initial Task so subsequent status/artifact events are valid.

    The 1.x task manager requires a ``Task`` to be enqueued before any
    ``TaskStatusUpdateEvent``; this seeds it in the ``submitted`` state.
    """
    task = Task(
        id=task_id,
        context_id=context_id,
        status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
    )
    await event_queue.enqueue_event(task)


def text_part(text: str) -> Part:
    """Build a plain-text A2A message part."""
    return Part(text=text)


def user_message(text: str) -> Message:
    """Build a user-role A2A message carrying a single text part."""
    import uuid

    return Message(
        message_id=uuid.uuid4().hex,
        role=Role.ROLE_USER,
        parts=[text_part(text)],
    )


def collect_text(parts: Iterable[Part]) -> str:
    """Concatenate the text of every text part in ``parts``."""
    chunks = [p.text for p in parts if p.text]
    return "\n".join(chunks).strip()


def extract_response_text(task_or_message: Task | Message) -> str:
    """Pull the agent's reply text out of a Task or a bare Message.

    For a Task we prefer artifact text (the canonical "result"), falling back
    to the status message and then the last history message.
    """
    if isinstance(task_or_message, Message):
        return collect_text(task_or_message.parts)

    task = task_or_message
    artifact_chunks: list[str] = []
    for artifact in task.artifacts:
        artifact_chunks.append(collect_text(artifact.parts))
    joined = "\n".join(c for c in artifact_chunks if c).strip()
    if joined:
        return joined

    if task.status and task.status.message and task.status.message.parts:
        status_text = collect_text(task.status.message.parts)
        if status_text:
            return status_text

    if task.history:
        return collect_text(task.history[-1].parts)
    return ""


def _peer_timeout_seconds() -> float:
    """Per-call timeout for peer A2A requests (configurable via env).

    A peer agent runs its own LLM reasoning before replying, so the default
    httpx timeout is far too short. Allow a generous window, overridable with
    ``A2A_CLIENT_TIMEOUT``.
    """
    try:
        return float(os.getenv("A2A_CLIENT_TIMEOUT", "120"))
    except ValueError:
        return 120.0


async def call_peer_agent(peer_url: str, message_text: str) -> str:
    """Send ``message_text`` to a peer agent and return its reply as text.

    Uses non-streaming mode so a single Task (with artifacts) comes back, then
    extracts the result text. The client is created per call and closed after.
    """
    httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(_peer_timeout_seconds()))
    config = ClientConfig(streaming=False, httpx_client=httpx_client)
    client = await create_client(peer_url, client_config=config)
    try:
        request = SendMessageRequest(message=user_message(message_text))
        reply = ""
        async for event in client.send_message(request):
            payload = event.WhichOneof("payload")
            if payload == "task":
                reply = extract_response_text(event.task)
            elif payload == "message":
                reply = extract_response_text(event.message)
            elif payload == "artifact_update":
                chunk = collect_text(event.artifact_update.artifact.parts)
                if chunk:
                    reply = chunk
            elif payload == "status_update":
                update = event.status_update
                if update.status and update.status.message:
                    chunk = collect_text(update.status.message.parts)
                    if chunk:
                        reply = chunk
        return reply
    finally:
        await client.close()
        await httpx_client.aclose()
