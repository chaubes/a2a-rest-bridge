"""Configurable chat-model factory shared by every agent.

The provider is selected with the ``LLM_PROVIDER`` environment variable
(default ``openai``). Importing this module never touches an API key; only
constructing and calling the OpenAI client requires ``OPENAI_API_KEY``.
"""

from __future__ import annotations

import os

from langchain_core.language_models import BaseChatModel


def make_llm(temperature: float = 0.0) -> BaseChatModel:
    """Build a chat model from the environment.

    * ``openai``  -> :class:`langchain_openai.ChatOpenAI`
      (model ``LLM_MODEL`` or ``gpt-4o-mini``); needs ``OPENAI_API_KEY``.
    * ``ollama``  -> :class:`langchain_ollama.ChatOllama`
      (model ``OLLAMA_MODEL`` or ``llama3.1`` at ``OLLAMA_BASE_URL``).

    The provider modules are imported lazily so that, for example, an Ollama
    deployment does not require any OpenAI credentials to be present.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=temperature,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=temperature,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER {provider!r}; expected 'openai' or 'ollama'."
    )
