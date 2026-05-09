"""Helpers for running the in-repo dbt transformation project."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    REPO_ROOT,
    ensure_db_service,
    get_postgres_settings,
    load_env_file,
    wait_for_database,
)


DBT_PROJECT_DIR = REPO_ROOT / "dbt"


def _dbt_command() -> list[str]:
    executable_path = Path(sys.executable)
    sibling_candidates = (
        executable_path.with_name("dbt.exe"),
        executable_path.with_name("dbt"),
    )
    for candidate in sibling_candidates:
        if candidate.exists():
            return [str(candidate)]

    discovered = shutil.which("dbt")
    if discovered:
        return [discovered]

    return [sys.executable, "-m", "dbt.cli.main"]


def run_dbt_build(selectors: Iterable[str], *, excludes: Iterable[str] | None = None) -> None:
    settings = get_postgres_settings()
    ensure_db_service()
    wait_for_database(settings)

    env = os.environ.copy()
    env.update(load_env_file())

    command = [
        *_dbt_command(),
        "build",
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--profiles-dir",
        str(DBT_PROJECT_DIR),
        "--target",
        "local",
        "--no-partial-parse",
        "--fail-fast",
        "--select",
        *selectors,
    ]
    if excludes:
        command.extend(["--exclude", *excludes])

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"dbt build failed ({result.returncode}).\nSTDOUT: {(result.stdout or '').strip()}\n"
            f"STDERR: {(result.stderr or '').strip()}"
        )
