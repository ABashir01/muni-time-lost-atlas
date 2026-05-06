"""Configuration helpers for the API package."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


@dataclass(frozen=True)
class ApiSettings:
    """Minimal API settings shared across future slices."""

    app_name: str = "Muni Lost Time Atlas API"
    environment: str = "development"
    database_url: str | None = None


def get_api_settings(environ: Mapping[str, str] | None = None) -> ApiSettings:
    """Read API settings from environment variables."""
    env = environ or os.environ
    return ApiSettings(
        environment=env.get("API_ENV", "development"),
        database_url=env.get("DATABASE_URL"),
    )
