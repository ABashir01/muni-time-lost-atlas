"""FastAPI application bootstrap for future API slices."""

from __future__ import annotations

from .config import ApiSettings, get_api_settings


def create_app(settings: ApiSettings | None = None):
    """Create the FastAPI application without defining endpoints yet."""
    from fastapi import FastAPI

    active_settings = settings or get_api_settings()
    app = FastAPI(title=active_settings.app_name)
    app.state.settings = active_settings
    return app
