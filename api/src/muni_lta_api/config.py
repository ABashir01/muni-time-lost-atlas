"""Configuration helpers for the API package."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


@dataclass(frozen=True)
class ApiSettings:
    """Minimal API settings shared across future slices."""

    app_name: str = "Muni Lost Time Atlas API"
    environment: str = "development"
    database_url: str | None = None


def load_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    """Load repo-local environment variables when present."""
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def build_database_url(env: Mapping[str, str]) -> str | None:
    """Build a Postgres URL from the shared local-development settings."""
    database_name = env.get("POSTGRES_DB")
    user = env.get("POSTGRES_USER")
    password = env.get("POSTGRES_PASSWORD")
    if not database_name or not user or password is None:
        return None

    host = env.get("POSTGRES_HOST", "127.0.0.1")
    port = env.get("POSTGRES_PORT", "5432")
    quoted_user = quote(user, safe="")
    quoted_password = quote(password, safe="")
    quoted_database = quote(database_name, safe="")
    return (
        f"postgresql://{quoted_user}:{quoted_password}@{host}:{port}/{quoted_database}"
    )


def get_api_settings(environ: Mapping[str, str] | None = None) -> ApiSettings:
    """Read API settings from environment variables."""
    env: dict[str, str] = {}
    env.update(load_env_file())
    env.update(os.environ)
    if environ:
        env.update(environ)

    return ApiSettings(
        environment=env.get("API_ENV", "development"),
        database_url=env.get("DATABASE_URL") or build_database_url(env),
    )
