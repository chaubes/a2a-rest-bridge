"""Shared infrastructure for the AgentCart MCP tool servers.

This package holds cross-cutting concerns reused by every tool server:
audit logging, the async HTTP client factory, correlation-id helpers,
OpenTelemetry tracing setup, and the per-correlation-id rate limiter.
"""
