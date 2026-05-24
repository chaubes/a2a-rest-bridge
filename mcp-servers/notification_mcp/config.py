"""Configuration for the notification MCP server."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    notification_service_url: str = "http://localhost:8084"


settings = NotificationSettings()

SERVICE_NAME = "notification-mcp"
PORT = 9005
