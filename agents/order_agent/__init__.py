"""Order A2A agent: the workflow orchestrator for AgentCart.

Drives the order lifecycle as a LangGraph ``StateGraph``, delegating to the
inventory, payment, shipping, and notification peer agents over A2A and saving
the order via the order MCP server directly.
"""
