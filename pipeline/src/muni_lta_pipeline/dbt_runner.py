"""Helpers for running the in-repo dbt transformation project."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Iterable, Mapping

from muni_lta_pipeline.config import get_pipeline_settings
from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    ensure_db_service,
    get_postgres_settings,
    load_env_file,
    wait_for_database,
)


APP_ROOT = get_pipeline_settings().app_root
DBT_PROJECT_DIR = APP_ROOT / "dbt"


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


def _run_dbt(
    command_name: str,
    selectors: Iterable[str],
    *,
    excludes: Iterable[str] | None = None,
    vars: Mapping[str, Any] | None = None,
) -> None:
    settings = get_postgres_settings()
    ensure_db_service()
    wait_for_database(settings)

    env = os.environ.copy()
    env.update(load_env_file())

    command = [
        *_dbt_command(),
        command_name,
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
    if vars:
        command.extend(["--vars", json.dumps(dict(vars), sort_keys=True)])

    process = subprocess.Popen(
        command,
        cwd=APP_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None
    output_lines: list[str] = []
    try:
        for line in process.stdout:
            print(line, end="", flush=True)
            output_lines.append(line)
    finally:
        process.stdout.close()

    returncode = process.wait()
    combined_output = "".join(output_lines).strip()
    if returncode != 0:
        raise RuntimeError(
            f"dbt {command_name} failed ({returncode}).\nSTDOUT: {combined_output}\nSTDERR: "
        )


def run_dbt_build(
    selectors: Iterable[str],
    *,
    excludes: Iterable[str] | None = None,
    vars: Mapping[str, Any] | None = None,
) -> None:
    _run_dbt("build", selectors, excludes=excludes, vars=vars)


def run_dbt_run(
    selectors: Iterable[str],
    *,
    excludes: Iterable[str] | None = None,
    vars: Mapping[str, Any] | None = None,
) -> None:
    _run_dbt("run", selectors, excludes=excludes, vars=vars)
