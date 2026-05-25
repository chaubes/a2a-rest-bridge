"""Configuration for the inventory MCP server."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class InventorySettings(BaseSettings):
    """Settings read from the environment (no secrets, only service URLs)."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    inventory_service_url: str = "http://localhost:8081"


settings = InventorySettings()

SERVICE_NAME = "inventory-mcp"
PORT = 9001
