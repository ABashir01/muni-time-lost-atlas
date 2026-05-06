"""Configuration helpers for the pipeline package."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class PipelineSettings:
    """Minimal pipeline settings shared across future slices."""

    environment: str = "development"
    database_url: str | None = None
    fixtures_root: Path = Path("fixtures")


def get_pipeline_settings(
    environ: Mapping[str, str] | None = None,
) -> PipelineSettings:
    """Read pipeline settings from environment variables."""
    env = environ or os.environ
    fixtures_root = Path(env.get("FIXTURES_ROOT", "fixtures"))
    return PipelineSettings(
        environment=env.get("PIPELINE_ENV", "development"),
        database_url=env.get("DATABASE_URL"),
        fixtures_root=fixtures_root,
    )
