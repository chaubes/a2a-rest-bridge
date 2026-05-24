"""OpenTelemetry tracing setup shared across the MCP tool servers.

Exposes:
  * ``configure_tracing`` — idempotently install a tracer provider whose
    exporter is selected by the ``OTEL_EXPORTER`` environment variable
    (``console`` by default), and auto-instrument the httpx client.
  * ``traced_tool`` — a decorator that wraps an async tool function in a span
    carrying ``mcp.correlation_id`` as an attribute.
"""

from __future__ import annotations

import functools
import os
import threading
from typing import Any, Awaitable, Callable, TypeVar

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

CORRELATION_SPAN_ATTRIBUTE = "mcp.correlation_id"

_configured_lock = threading.Lock()
_configured = False


def _build_exporter() -> Any:
    """Build a span exporter chosen by the ``OTEL_EXPORTER`` env var."""
    exporter_name = os.getenv("OTEL_EXPORTER", "console").strip().lower()
    if exporter_name == "otlp":
        # Imported lazily so the console path has no gRPC dependency at import.
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            return OTLPSpanExporter(endpoint=endpoint)
        return OTLPSpanExporter()
    # Default and fallback: print spans to stdout.
    return ConsoleSpanExporter()


def configure_tracing(service_name: str) -> trace.Tracer:
    """Install the tracer provider and instrument httpx exactly once.

    Safe to call from every server at startup; subsequent calls only return a
    tracer scoped to ``service_name`` without re-installing the provider.
    """
    global _configured
    with _configured_lock:
        if not _configured:
            resource = Resource.create({"service.name": service_name})
            provider = TracerProvider(resource=resource)

            exporter = _build_exporter()
            if isinstance(exporter, ConsoleSpanExporter):
                provider.add_span_processor(SimpleSpanProcessor(exporter))
            else:
                provider.add_span_processor(BatchSpanProcessor(exporter))

            trace.set_tracer_provider(provider)

            # Auto-instrument outbound httpx calls so REST requests become
            # child spans of the tool span.
            try:
                from opentelemetry.instrumentation.httpx import (
                    HTTPXClientInstrumentor,
                )

                HTTPXClientInstrumentor().instrument()
            except Exception:
                # Instrumentation is best-effort; tracing of the tool span
                # itself must not fail if httpx instrumentation is unavailable.
                pass

            _configured = True

    return trace.get_tracer(service_name)


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def traced_tool(tool_name: str) -> Callable[[F], F]:
    """Wrap an async tool function in a span named after the tool.

    The decorated function must accept a ``correlation_id`` keyword (or
    positional) argument; its value is attached to the span as
    ``mcp.correlation_id``.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(tool_name)
            correlation_id = kwargs.get("correlation_id", "")
            with tracer.start_as_current_span(f"mcp.tool.{tool_name}") as span:
                span.set_attribute(CORRELATION_SPAN_ATTRIBUTE, correlation_id)
                span.set_attribute("mcp.tool", tool_name)
                return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
