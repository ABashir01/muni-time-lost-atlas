"""Fetch, load, and materialize the bounded real historical cutover dataset."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import psycopg

from muni_lta_pipeline.active_gtfs_fetch import (
    DEFAULT_ACQUISITIONS_ROOT as ACTIVE_GTFS_ACQUISITIONS_ROOT,
    fetch_active_gtfs_archive,
    get_511_api_key,
)
from muni_lta_pipeline.dbt_runner import run_dbt_run
from muni_lta_pipeline.gtfs_archive_ingest import (
    build_archive_snapshot_label as build_gtfs_archive_snapshot_label,
    load_gtfs_archive,
)
from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    REPO_ROOT,
    build_postgres_connection_url,
    get_postgres_settings,
    run_psql_sql,
)
from muni_lta_pipeline.historic_rg_feed_fetch import (
    DEFAULT_ACQUISITIONS_ROOT as HISTORIC_GTFS_ACQUISITIONS_ROOT,
    fetch_historic_rg_gtfs_archive,
)
from muni_lta_pipeline.historic_rg_sf_extract import extract_sf_historic_archive
from muni_lta_pipeline.historic_stop_observations_archive_ingest import (
    build_archive_snapshot_label as build_observed_archive_snapshot_label,
    load_historic_stop_observations_archive,
)
from muni_lta_pipeline.transit_lane_overlay_fixture_ingest import (
    DEFAULT_FIXTURE_PATH as TRANSIT_LANE_OVERLAY_FIXTURE_PATH,
    load_transit_lane_overlay_fixture,
)


DEFAULT_HISTORIC_MONTH = "2023-02"
DEFAULT_HISTORIC_AGENCY_ID = "SF"
DEFAULT_CUTOVER_ROOT = (
    REPO_ROOT / "artifacts" / "cutovers" / "b6a_real_dataset_cutover_bundle"
)


@dataclass(frozen=True)
class RealDatasetCutoverResult:
    active_gtfs_metadata_path: Path
    active_gtfs_snapshot_label: str
    historic_source_metadata_path: Path
    historic_gtfs_metadata_path: Path
    historic_gtfs_snapshot_label: str
    historic_observed_snapshot_label: str
    historic_month: str
    historic_agency_id: str
    log_path: Path
    latest_log_path: Path
    overlay_row_count: int
    reused_existing_gtfs_raw: bool
    reused_existing_observed_raw: bool
    reused_existing_overlay_raw: bool
    reused_existing_dbt: bool
    skipped_dbt: bool
    dbt_action: str
    dbt_fingerprint: dict[str, Any]
    route_count_with_metrics: int
    map_route_count: int
    top_route_ids: list[str]
    dbt_vars: dict[str, str]
    manifest_path: Path
    latest_manifest_path: Path


def _query_int(connection: psycopg.Connection[Any], sql: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("Expected a row from integer query.")
    return int(row[0])


def _table_exists(connection: psycopg.Connection[Any], *, schema: str, table: str) -> bool:
    return _query_int(
        connection,
        f"""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
          AND table_name = '{table}';
        """,
    ) > 0


def _snapshot_row_count(
    connection: psycopg.Connection[Any],
    table_name: str,
    snapshot_label: str,
) -> int:
    return _query_int(
        connection,
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE snapshot_label = '{snapshot_label.replace("'", "''")}';
        """,
    )


def _snapshot_exists(
    connection: psycopg.Connection[Any],
    table_name: str,
    snapshot_label: str,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT EXISTS (
                SELECT 1
                FROM {table_name}
                WHERE snapshot_label = '{snapshot_label.replace("'", "''")}'
                LIMIT 1
            );
            """
        )
        row = cursor.fetchone()
    return bool(row and row[0])


def _gtfs_snapshot_present(connection: psycopg.Connection[Any], snapshot_label: str) -> bool:
    required_tables = (
        "raw.gtfs_routes",
        "raw.gtfs_trips",
        "raw.gtfs_stops",
        "raw.gtfs_stop_times",
        "raw.gtfs_shapes",
    )
    required_table_names = (
        ("raw", "gtfs_routes"),
        ("raw", "gtfs_trips"),
        ("raw", "gtfs_stops"),
        ("raw", "gtfs_stop_times"),
        ("raw", "gtfs_shapes"),
        ("raw", "gtfs_calendar"),
        ("raw", "gtfs_calendar_dates"),
    )
    if any(
        not _table_exists(connection, schema=schema, table=table)
        for schema, table in required_table_names
    ):
        return False
    if any(
        not _snapshot_exists(connection, table_name, snapshot_label)
        for table_name in required_tables
    ):
        return False

    return _snapshot_exists(connection, "raw.gtfs_calendar", snapshot_label) or _snapshot_exists(
        connection,
        "raw.gtfs_calendar_dates",
        snapshot_label,
    )


def _stop_observations_snapshot_present(
    connection: psycopg.Connection[Any],
    snapshot_label: str,
) -> bool:
    if not _table_exists(connection, schema="raw", table="stop_observations"):
        return False
    return _snapshot_exists(connection, "raw.stop_observations", snapshot_label)


def _overlay_snapshot_present(
    connection: psycopg.Connection[Any],
    snapshot_label: str,
) -> bool:
    if not _table_exists(connection, schema="raw", table="transit_only_lanes"):
        return False
    return _snapshot_exists(connection, "raw.transit_only_lanes", snapshot_label)


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _compute_dbt_fingerprint(
    dbt_vars: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    tracked_paths: list[str] = []
    candidates: list[Path] = []
    dbt_project_path = repo_root / "dbt_project.yml"
    if dbt_project_path.exists():
        candidates.append(dbt_project_path)
    for relative_dir in ("dbt/models", "dbt/macros"):
        root = repo_root / relative_dir
        if root.exists():
            candidates.extend(path for path in root.rglob("*") if path.is_file())

    for path in sorted(candidates, key=lambda candidate: str(candidate.relative_to(repo_root))):
        relative_path = path.relative_to(repo_root).as_posix()
        tracked_paths.append(relative_path)
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    digest.update(b"dbt_vars\0")
    digest.update(_canonical_json(dbt_vars).encode("utf-8"))
    return {
        "sha256": digest.hexdigest(),
        "tracked_paths": tracked_paths,
    }


def _compute_raw_input_fingerprint(
    *,
    active_metadata_path: Path,
    historic_metadata_path: Path,
    overlay_fixture_path: Path = TRANSIT_LANE_OVERLAY_FIXTURE_PATH,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    tracked_inputs: list[str] = []

    for label, metadata_path in (
        ("active_metadata", active_metadata_path),
        ("historic_metadata", historic_metadata_path),
    ):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        tracked_inputs.append(str(metadata_path))
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(metadata_path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(_canonical_json(payload).encode("utf-8"))
        digest.update(b"\0")

    tracked_inputs.append(str(overlay_fixture_path))
    digest.update(b"overlay_fixture\0")
    digest.update(str(overlay_fixture_path).encode("utf-8"))
    digest.update(b"\0")
    digest.update(overlay_fixture_path.read_bytes())

    return {
        "sha256": digest.hexdigest(),
        "tracked_inputs": tracked_inputs,
    }


def _raw_snapshot_labels(
    *,
    active_gtfs_snapshot_label: str,
    historic_gtfs_snapshot_label: str,
    historic_observed_snapshot_label: str,
    overlay_snapshot_label: str,
) -> dict[str, str]:
    return {
        "active_gtfs_snapshot_label": active_gtfs_snapshot_label,
        "historic_gtfs_snapshot_label": historic_gtfs_snapshot_label,
        "historic_observed_snapshot_label": historic_observed_snapshot_label,
        "overlay_snapshot_label": overlay_snapshot_label,
    }


def _manifest_raw_snapshot_labels(manifest: dict[str, Any]) -> dict[str, str]:
    if isinstance(manifest.get("raw_snapshot_labels"), dict):
        labels = manifest["raw_snapshot_labels"]
        return {
            "active_gtfs_snapshot_label": str(labels.get("active_gtfs_snapshot_label", "")),
            "historic_gtfs_snapshot_label": str(labels.get("historic_gtfs_snapshot_label", "")),
            "historic_observed_snapshot_label": str(
                labels.get("historic_observed_snapshot_label", "")
            ),
            "overlay_snapshot_label": str(labels.get("overlay_snapshot_label", "")),
        }

    return {
        "active_gtfs_snapshot_label": str(manifest.get("active_gtfs_snapshot_label", "")),
        "historic_gtfs_snapshot_label": str(manifest.get("historic_gtfs_snapshot_label", "")),
        "historic_observed_snapshot_label": str(
            manifest.get("historic_observed_snapshot_label", "")
        ),
        "overlay_snapshot_label": str(manifest.get("overlay_snapshot_label", "")),
    }


def _manifest_dbt_fingerprint_sha(manifest: dict[str, Any]) -> str | None:
    fingerprint = manifest.get("dbt_fingerprint")
    if isinstance(fingerprint, dict):
        sha256 = fingerprint.get("sha256")
        if sha256:
            return str(sha256)
    if isinstance(fingerprint, str) and fingerprint:
        return fingerprint
    return None


def _manifest_raw_input_fingerprint_sha(manifest: dict[str, Any]) -> str | None:
    fingerprint = manifest.get("raw_input_fingerprint")
    if isinstance(fingerprint, dict):
        sha256 = fingerprint.get("sha256")
        if sha256:
            return str(sha256)
    if isinstance(fingerprint, str) and fingerprint:
        return fingerprint
    return None


def _manifest_completed_dbt(manifest: dict[str, Any]) -> bool:
    dbt_action = manifest.get("dbt_action")
    if isinstance(dbt_action, str):
        return dbt_action in {"run", "reused_existing"}
    return not bool(manifest.get("skipped_dbt", False))


def _manifest_self_path(manifest_path: Path, manifest: dict[str, Any]) -> Path:
    recorded_manifest_path = manifest.get("manifest_path")
    if isinstance(recorded_manifest_path, str) and recorded_manifest_path:
        return Path(recorded_manifest_path)
    return manifest_path


def _iter_prior_manifest_paths(cutover_root: Path) -> list[Path]:
    if not cutover_root.exists():
        return []

    manifest_paths: list[Path] = []
    latest_manifest_path = cutover_root / "latest.json"
    if latest_manifest_path.exists():
        manifest_paths.append(latest_manifest_path)

    manifest_paths.extend(
        path
        for path in sorted(cutover_root.glob("*.json"), reverse=True)
        if path.name != "latest.json"
    )
    return manifest_paths


def _find_reusable_dbt_manifest(
    *,
    cutover_root: Path,
    raw_snapshot_labels: dict[str, str],
    raw_input_fingerprint: dict[str, Any],
    dbt_vars: dict[str, Any],
    dbt_fingerprint: dict[str, Any],
) -> tuple[Path, dict[str, Any]] | None:
    for manifest_path in _iter_prior_manifest_paths(cutover_root):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not _manifest_completed_dbt(manifest):
            continue
        if _manifest_raw_snapshot_labels(manifest) != raw_snapshot_labels:
            continue
        if _manifest_raw_input_fingerprint_sha(manifest) != raw_input_fingerprint["sha256"]:
            continue
        if manifest.get("dbt_vars") != dbt_vars:
            continue
        if _manifest_dbt_fingerprint_sha(manifest) != dbt_fingerprint["sha256"]:
            continue
        return manifest_path, manifest

    return None


def _log(message: str, *, log_path: Path, latest_log_path: Path) -> None:
    timestamped = f"{datetime.now(tz=UTC).isoformat()} {message}"
    print(timestamped, flush=True)
    for path in (log_path, latest_log_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(timestamped)
            handle.write("\n")


def _find_reusable_raw_manifest(
    *,
    cutover_root: Path,
    raw_snapshot_labels: dict[str, str],
    raw_input_fingerprint: dict[str, Any],
) -> tuple[Path, dict[str, Any]] | None:
    for manifest_path in _iter_prior_manifest_paths(cutover_root):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _manifest_raw_snapshot_labels(manifest) != raw_snapshot_labels:
            continue
        if _manifest_raw_input_fingerprint_sha(manifest) != raw_input_fingerprint["sha256"]:
            continue
        return manifest_path, manifest
    return None


def materialize_real_dataset_cutover(
    *,
    historic_month: str = DEFAULT_HISTORIC_MONTH,
    historic_agency_id: str = DEFAULT_HISTORIC_AGENCY_ID,
    active_metadata_path: Path | None = None,
    historic_metadata_path: Path | None = None,
    cutover_root: Path = DEFAULT_CUTOVER_ROOT,
    reuse_existing_raw: bool = True,
    skip_dbt: bool = False,
) -> RealDatasetCutoverResult:
    run_timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = cutover_root / f"{run_timestamp}.log"
    latest_log_path = cutover_root / "latest.log"
    latest_log_path.parent.mkdir(parents=True, exist_ok=True)
    latest_log_path.write_text("", encoding="utf-8")
    _log(
        f"starting real dataset cutover for historic_month={historic_month} historic_agency_id={historic_agency_id}",
        log_path=log_path,
        latest_log_path=latest_log_path,
    )

    api_key: str | None = None

    if active_metadata_path is None:
        if api_key is None:
            api_key = get_511_api_key()
        _log(
            "fetching active GTFS acquisition metadata",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )
        active_result = fetch_active_gtfs_archive(
            api_key=api_key,
            acquisitions_root=ACTIVE_GTFS_ACQUISITIONS_ROOT,
        )
        active_metadata_path = active_result.metadata_path
    else:
        _log(
            f"reusing active GTFS metadata {active_metadata_path}",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )

    if historic_metadata_path is None:
        if api_key is None:
            api_key = get_511_api_key()
        _log(
            "fetching historic RG -so acquisition metadata",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )
        historic_result = fetch_historic_rg_gtfs_archive(
            api_key=api_key,
            historic_month=historic_month,
            include_stop_observations=True,
            acquisitions_root=HISTORIC_GTFS_ACQUISITIONS_ROOT,
        )
        historic_metadata_path = historic_result.metadata_path
    else:
        _log(
            f"reusing historic RG metadata {historic_metadata_path}",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )

    historic_source_metadata_path = historic_metadata_path
    historic_sf_result = extract_sf_historic_archive(
        metadata_path=historic_metadata_path,
        selected_agency_id=historic_agency_id,
        api_key=api_key,
        active_metadata_path=active_metadata_path,
    )
    historic_metadata_path = historic_sf_result.metadata_path
    _log(
        "prepared SF-only historic archive "
        f"metadata={historic_metadata_path} reused_existing={historic_sf_result.reused_existing} "
        f"retained_row_counts={historic_sf_result.metadata.retained_row_counts}",
        log_path=log_path,
        latest_log_path=latest_log_path,
    )

    return materialize_prepared_historic_publication(
        active_metadata_path=active_metadata_path,
        historic_source_metadata_path=historic_source_metadata_path,
        historic_gtfs_metadata_path=historic_metadata_path,
        historic_feed_scope=historic_sf_result.metadata.feed_scope,
        historic_month=historic_month,
        historic_agency_id=historic_agency_id,
        cutover_root=cutover_root,
        log_path=log_path,
        latest_log_path=latest_log_path,
        reuse_existing_raw=reuse_existing_raw,
        skip_dbt=skip_dbt,
        shape_fallback_metadata={
            "shape_backfill_cache_hits": getattr(
                historic_sf_result.metadata, "shape_backfill_cache_hits", 0
            ),
            "shape_backfill_failure_count": getattr(
                historic_sf_result.metadata, "shape_backfill_failure_count", 0
            ),
            "shape_backfill_manifest_path": getattr(
                historic_sf_result.metadata, "shape_backfill_manifest_path", ""
            ),
            "shape_backfill_request_count": getattr(
                historic_sf_result.metadata, "shape_backfill_request_count", 0
            ),
            "shape_backfill_shape_count": getattr(
                historic_sf_result.metadata, "shape_backfill_shape_count", 0
            ),
            "shape_backfill_trip_selection_strategy": getattr(
                historic_sf_result.metadata,
                "shape_backfill_trip_selection_strategy",
                "unique_active_shape_then_shapes_api",
            ),
            "shape_fallback_used": getattr(
                historic_sf_result.metadata,
                "shape_fallback_used",
                False,
            ),
        },
    )


def materialize_prepared_historic_publication(
    *,
    active_metadata_path: Path,
    historic_source_metadata_path: Path,
    historic_gtfs_metadata_path: Path,
    historic_feed_scope: str,
    historic_month: str,
    historic_agency_id: str,
    cutover_root: Path,
    log_path: Path,
    latest_log_path: Path,
    reuse_existing_raw: bool = True,
    skip_dbt: bool = False,
    shape_fallback_metadata: Mapping[str, Any] | None = None,
    manifest_extra: Mapping[str, Any] | None = None,
) -> RealDatasetCutoverResult:
    shape_fallback_metadata = dict(shape_fallback_metadata or {})
    manifest_extra = dict(manifest_extra or {})

    active_gtfs_snapshot_label = build_gtfs_archive_snapshot_label(
        json.loads(active_metadata_path.read_text(encoding="utf-8"))
    )
    historic_gtfs_snapshot_label = build_gtfs_archive_snapshot_label(
        json.loads(historic_gtfs_metadata_path.read_text(encoding="utf-8"))
    )
    historic_observed_snapshot_label = build_observed_archive_snapshot_label(
        json.loads(historic_gtfs_metadata_path.read_text(encoding="utf-8"))
    )
    overlay_snapshot_label = "fixture_transit_lanes_v1"
    raw_snapshot_labels = _raw_snapshot_labels(
        active_gtfs_snapshot_label=active_gtfs_snapshot_label,
        historic_gtfs_snapshot_label=historic_gtfs_snapshot_label,
        historic_observed_snapshot_label=historic_observed_snapshot_label,
        overlay_snapshot_label=overlay_snapshot_label,
    )
    raw_input_fingerprint = _compute_raw_input_fingerprint(
        active_metadata_path=active_metadata_path,
        historic_metadata_path=historic_gtfs_metadata_path,
    )
    reusable_raw_manifest = _find_reusable_raw_manifest(
        cutover_root=cutover_root,
        raw_snapshot_labels=raw_snapshot_labels,
        raw_input_fingerprint=raw_input_fingerprint,
    )

    reused_existing_gtfs_raw = False
    reused_existing_observed_raw = False
    reused_existing_overlay_raw = False
    connection_url = build_postgres_connection_url()
    with psycopg.connect(connection_url) as metadata_connection:
        if reuse_existing_raw and (
            _gtfs_snapshot_present(metadata_connection, active_gtfs_snapshot_label)
            and _gtfs_snapshot_present(metadata_connection, historic_gtfs_snapshot_label)
        ) and reusable_raw_manifest is not None:
            reused_existing_gtfs_raw = True
            reused_raw_manifest_path = _manifest_self_path(
                reusable_raw_manifest[0],
                reusable_raw_manifest[1],
            )
            _log(
                "reusing existing raw GTFS snapshots "
                f"{active_gtfs_snapshot_label} and {historic_gtfs_snapshot_label} "
                f"because raw input fingerprint matches manifest {reused_raw_manifest_path}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
        else:
            _log(
                f"loading active GTFS archive from {active_metadata_path}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
            active_gtfs_load = load_gtfs_archive(
                metadata_path=active_metadata_path,
                truncate=True,
            )
            _log(
                f"loaded active GTFS snapshot {active_gtfs_load.snapshot_label} with tables={active_gtfs_load.inserted_row_counts}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )

            _log(
                f"loading historic GTFS archive from {historic_gtfs_metadata_path}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
            historic_gtfs_load = load_gtfs_archive(
                metadata_path=historic_gtfs_metadata_path,
                truncate=False,
            )
            _log(
                f"loaded historic GTFS snapshot {historic_gtfs_load.snapshot_label} with tables={historic_gtfs_load.inserted_row_counts}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )

        if reuse_existing_raw and _stop_observations_snapshot_present(
            metadata_connection,
            historic_observed_snapshot_label,
        ) and reusable_raw_manifest is not None:
            reused_existing_observed_raw = True
            _log(
                "reusing existing raw stop observations snapshot "
                f"{historic_observed_snapshot_label} because raw input fingerprint matches",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
        else:
            _log(
                f"loading historic stop observations from {historic_gtfs_metadata_path}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
            historic_observed_load = load_historic_stop_observations_archive(
                metadata_path=historic_gtfs_metadata_path,
                truncate=True,
            )
            _log(
                "loaded historic stop observations "
                f"snapshot {historic_observed_load.snapshot_label} rows={historic_observed_load.inserted_row_count} "
                f"skipped_missing_required={historic_observed_load.skipped_missing_required_count}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )

        if (
            reuse_existing_raw
            and _overlay_snapshot_present(metadata_connection, overlay_snapshot_label)
            and reusable_raw_manifest is not None
        ):
            reused_existing_overlay_raw = True
            overlay_row_count = _snapshot_row_count(
                metadata_connection,
                "raw.transit_only_lanes",
                overlay_snapshot_label,
            )
            _log(
                f"reusing existing transit lane overlay snapshot {overlay_snapshot_label} rows={overlay_row_count}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
        else:
            _log(
                "loading transit lane overlay fixture",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )
            overlay_row_count = load_transit_lane_overlay_fixture(
                fixture_path=TRANSIT_LANE_OVERLAY_FIXTURE_PATH,
                snapshot_label=overlay_snapshot_label,
            )
            _log(
                f"loaded transit lane overlay rows={overlay_row_count}",
                log_path=log_path,
                latest_log_path=latest_log_path,
            )

    dbt_vars = {
        "gtfs_feed_scope": historic_feed_scope,
        "gtfs_snapshot_label": historic_gtfs_snapshot_label,
        "historic_agency_id": historic_agency_id,
        "metrics_intermediate_materialization": "table",
        "observed_feed_scope": historic_feed_scope,
        "observed_canonical_materialization": "table",
        "observed_snapshot_label": historic_observed_snapshot_label,
        "performance_indexing": True,
    }
    dbt_fingerprint = _compute_dbt_fingerprint(dbt_vars)
    reusable_dbt_manifest = _find_reusable_dbt_manifest(
        cutover_root=cutover_root,
        raw_snapshot_labels=raw_snapshot_labels,
        raw_input_fingerprint=raw_input_fingerprint,
        dbt_vars=dbt_vars,
        dbt_fingerprint=dbt_fingerprint,
    )
    reused_existing_dbt = False
    dbt_action = "run"

    if skip_dbt:
        dbt_action = "skipped_by_request"
        _log(
            "skipping dbt run by request",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )
    elif reusable_dbt_manifest is not None:
        reused_existing_dbt = True
        dbt_action = "reused_existing"
        reused_manifest_path, reused_manifest = reusable_dbt_manifest
        reused_manifest_path = _manifest_self_path(reused_manifest_path, reused_manifest)
        _log(
            "skipping dbt run because raw snapshot labels, raw input fingerprint, dbt vars, "
            f"and dbt fingerprint match successful manifest {reused_manifest_path}",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )
    else:
        _log(
            f"starting dbt run with vars={json.dumps(dbt_vars, sort_keys=True)}",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )
        run_dbt_run(
            [
                "path:models/staging",
                "path:models/canonical",
                "path:models/marts",
                "path:models/serving",
            ],
            vars=dbt_vars,
        )
        _log(
            "dbt run completed successfully",
            log_path=log_path,
            latest_log_path=latest_log_path,
        )

    _log(
        "querying app-facing route coverage counts",
        log_path=log_path,
        latest_log_path=latest_log_path,
    )
    with psycopg.connect(connection_url) as query_connection:
        route_count_with_metrics = _query_int(
            query_connection,
            """
            SELECT COUNT(*)
            FROM marts.route_window_summary
            WHERE typical_trip_loss_minutes IS NOT NULL;
            """,
        )
        map_route_count = _query_int(
            query_connection,
            "SELECT COUNT(*) FROM serving.route_map_layer;",
        )
        with query_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT route_id
                FROM marts.route_window_summary
                WHERE typical_trip_loss_minutes IS NOT NULL
                ORDER BY typical_trip_loss_minutes DESC NULLS LAST, route_id
                LIMIT 10;
                """
            )
            top_route_ids = [str(row[0]) for row in cursor.fetchall()]
    _log(
        f"route_count_with_metrics={route_count_with_metrics} map_route_count={map_route_count} top_route_ids={top_route_ids}",
        log_path=log_path,
        latest_log_path=latest_log_path,
    )

    run_timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest_path = cutover_root / f"{run_timestamp}.json"
    latest_manifest_path = cutover_root / "latest.json"
    manifest_payload = {
        "active_gtfs_metadata_path": str(active_metadata_path),
        "active_gtfs_snapshot_label": active_gtfs_snapshot_label,
        "cutover_built_at": datetime.now(tz=UTC).isoformat(),
        "dbt_vars": dbt_vars,
        "dbt_action": dbt_action,
        "dbt_fingerprint": dbt_fingerprint,
        "historic_agency_id": historic_agency_id,
        "historic_source_metadata_path": str(historic_source_metadata_path),
        "historic_gtfs_metadata_path": str(historic_gtfs_metadata_path),
        "historic_gtfs_snapshot_label": historic_gtfs_snapshot_label,
        "historic_month": historic_month,
        "historic_observed_snapshot_label": historic_observed_snapshot_label,
        "latest_log_path": str(latest_log_path),
        "latest_manifest_path": str(latest_manifest_path),
        "log_path": str(log_path),
        "map_route_count": map_route_count,
        "manifest_path": str(manifest_path),
        "overlay_snapshot_label": overlay_snapshot_label,
        "overlay_row_count": overlay_row_count,
        "raw_snapshot_labels": raw_snapshot_labels,
        "raw_input_fingerprint": raw_input_fingerprint,
        "reused_existing_dbt": reused_existing_dbt,
        "reused_existing_gtfs_raw": reused_existing_gtfs_raw,
        "reused_existing_observed_raw": reused_existing_observed_raw,
        "reused_existing_overlay_raw": reused_existing_overlay_raw,
        "shape_backfill_cache_hits": shape_fallback_metadata.get("shape_backfill_cache_hits", 0),
        "shape_backfill_failure_count": shape_fallback_metadata.get("shape_backfill_failure_count", 0),
        "shape_backfill_manifest_path": shape_fallback_metadata.get("shape_backfill_manifest_path", ""),
        "shape_backfill_request_count": shape_fallback_metadata.get("shape_backfill_request_count", 0),
        "shape_backfill_shape_count": shape_fallback_metadata.get("shape_backfill_shape_count", 0),
        "shape_backfill_trip_selection_strategy": shape_fallback_metadata.get(
            "shape_backfill_trip_selection_strategy",
            "unique_active_shape_then_shapes_api",
        ),
        "shape_fallback_used": shape_fallback_metadata.get("shape_fallback_used", False),
        "skipped_dbt": skip_dbt or reused_existing_dbt,
        "route_count_with_metrics": route_count_with_metrics,
        "top_route_ids": top_route_ids,
    }
    if reusable_dbt_manifest is not None:
        manifest_payload["dbt_reuse_manifest_path"] = str(
            _manifest_self_path(reusable_dbt_manifest[0], reusable_dbt_manifest[1])
        )
    else:
        manifest_payload["dbt_reuse_manifest_path"] = None
    manifest_payload.update(manifest_extra)
    _write_manifest(manifest_path, manifest_payload)
    _write_manifest(latest_manifest_path, manifest_payload)
    _log(
        f"wrote manifests to {manifest_path} and {latest_manifest_path}",
        log_path=log_path,
        latest_log_path=latest_log_path,
    )

    return RealDatasetCutoverResult(
        active_gtfs_metadata_path=active_metadata_path,
        active_gtfs_snapshot_label=active_gtfs_snapshot_label,
        historic_source_metadata_path=historic_source_metadata_path,
        historic_gtfs_metadata_path=historic_gtfs_metadata_path,
        historic_gtfs_snapshot_label=historic_gtfs_snapshot_label,
        historic_observed_snapshot_label=historic_observed_snapshot_label,
        historic_month=historic_month,
        historic_agency_id=historic_agency_id,
        log_path=log_path,
        latest_log_path=latest_log_path,
        overlay_row_count=overlay_row_count,
        reused_existing_gtfs_raw=reused_existing_gtfs_raw,
        reused_existing_observed_raw=reused_existing_observed_raw,
        reused_existing_overlay_raw=reused_existing_overlay_raw,
        reused_existing_dbt=reused_existing_dbt,
        skipped_dbt=skip_dbt or reused_existing_dbt,
        dbt_action=dbt_action,
        dbt_fingerprint=dbt_fingerprint,
        route_count_with_metrics=route_count_with_metrics,
        map_route_count=map_route_count,
        top_route_ids=top_route_ids,
        dbt_vars=dbt_vars,
        manifest_path=manifest_path,
        latest_manifest_path=latest_manifest_path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--historic-month",
        default=DEFAULT_HISTORIC_MONTH,
        help="Bounded historic RG archive month in YYYY-MM format.",
    )
    parser.add_argument(
        "--historic-agency-id",
        default=DEFAULT_HISTORIC_AGENCY_ID,
        help="Agency id to isolate inside the regional historic archive.",
    )
    parser.add_argument(
        "--active-metadata-path",
        type=Path,
        default=None,
        help="Reuse an existing active GTFS acquisition sidecar instead of fetching again.",
    )
    parser.add_argument(
        "--historic-metadata-path",
        type=Path,
        default=None,
        help="Reuse an existing historic RG -so acquisition sidecar instead of fetching again.",
    )
    parser.add_argument(
        "--cutover-root",
        type=Path,
        default=DEFAULT_CUTOVER_ROOT,
        help="Directory where the cutover manifest should be written.",
    )
    parser.add_argument(
        "--force-raw-reload",
        action="store_true",
        help="Reload raw GTFS, observations, and overlay inputs even when the target snapshots already exist.",
    )
    parser.add_argument(
        "--skip-dbt",
        action="store_true",
        help="Prepare artifacts and raw tables only, without rebuilding the dbt graph.",
    )
    args = parser.parse_args()

    result = materialize_real_dataset_cutover(
        historic_month=args.historic_month,
        historic_agency_id=args.historic_agency_id,
        active_metadata_path=args.active_metadata_path,
        historic_metadata_path=args.historic_metadata_path,
        cutover_root=args.cutover_root,
        reuse_existing_raw=not args.force_raw_reload,
        skip_dbt=args.skip_dbt,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
