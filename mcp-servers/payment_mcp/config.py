"""Configuration for the payment MCP server."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    payment_service_url: str = "http://localhost:8082"


settings = PaymentSettings()

SERVICE_NAME = "payment-mcp"
PORT = 9002
