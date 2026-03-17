"""Application settings loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the ticket dashboard.

    All values are sourced from environment variables or a .env file.
    See .env.example for documentation of each variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Dashboard data
    data_csv_path: Optional[str] = Field(
        default=None,
        description="Absolute path to ServiceNow CSV export. Uses mock data if unset.",
    )

    # Runtime
    environment: str = Field(
        default="local",
        description="Runtime environment: local | staging | production.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity: DEBUG | INFO | WARNING | ERROR.",
    )

    # Dashboard server
    dashboard_host: str = Field(default="0.0.0.0", description="Bind host for the Dash server.")
    dashboard_port: int = Field(default=8050, description="Bind port for the Dash server.")

    # Hardware (Raspberry Pi)
    hardware_enabled: bool = Field(
        default=False,
        description="Set true on Pi hardware to enable GPIO layer.",
    )
