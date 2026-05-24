"""ReAct agent builder for the shipping agent."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from shipping_agent.prompts import SYSTEM_PROMPT


def build_react_agent(model: BaseChatModel, tools: list[BaseTool]):
    """Build the shipping ReAct agent over the supplied model and tools."""
    return create_react_agent(model, tools, prompt=SYSTEM_PROMPT)
