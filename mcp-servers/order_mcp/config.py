"""Configuration for the order MCP server."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrderSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    order_service_url: str = "http://localhost:8080"


settings = OrderSettings()

SERVICE_NAME = "order-mcp"
PORT = 9004
