"""Configuration for the shipping MCP server."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ShippingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    shipping_service_url: str = "http://localhost:8083"


settings = ShippingSettings()

SERVICE_NAME = "shipping-mcp"
PORT = 9003
