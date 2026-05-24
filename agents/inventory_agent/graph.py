"""ReAct agent builder for the inventory agent.

The peer agents do not need a bespoke ``StateGraph``; their logic is a single
tool-using ReAct loop. This module exposes a builder so the executor (and tests)
can construct the agent with explicit tools and model.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from inventory_agent.prompts import SYSTEM_PROMPT


def build_react_agent(model: BaseChatModel, tools: list[BaseTool]):
    """Build the inventory ReAct agent over the supplied model and tools."""
    return create_react_agent(model, tools, prompt=SYSTEM_PROMPT)
