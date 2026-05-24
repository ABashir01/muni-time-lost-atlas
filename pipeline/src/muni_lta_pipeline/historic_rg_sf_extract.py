"""Derive an SF-only historic GTFS archive from a fetched regional RG archive."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from io import StringIO, TextIOWrapper
from pathlib import Path
from typing import Any, Mapping
import zipfile

from muni_lta_pipeline.active_gtfs_fetch import CORE_GTFS_FILES, get_511_api_key
from muni_lta_pipeline.gtfs_static_fixture_ingest import REPO_ROOT
from muni_lta_pipeline.historic_rg_feed_fetch import STOP_OBSERVATIONS_FILENAME
from muni_lta_pipeline.historic_shapes_api import (
    backfill_missing_shapes,
    normalize_trip_id_for_shapes_api,
)


DEFAULT_DERIVED_ACQUISITIONS_ROOT = (
    REPO_ROOT / "artifacts" / "acquisitions" / "511" / "regional_historic_sf"
)
DEFAULT_SHAPES_CACHE_ROOT = REPO_ROOT / "artifacts" / "acquisitions" / "511" / "shapes_api"
DEFAULT_SELECTED_AGENCY_ID = "SF"
DERIVED_FEED_SCOPE = "regional_historic_sf"
OPTIONAL_GTFS_FILES = ("calendar.txt", "calendar_dates.txt")
CURRENT_SHAPE_FALLBACK_STRATEGY = "unique_active_shape_then_shapes_api"


@dataclass(frozen=True)
class HistoricSfExtractionMetadata:
    artifact_filename: str
    artifact_sha256: str
    artifact_size_bytes: int
    derived_at: str
    feed_scope: str
    operator_id: str
    requested_historic_month: str
    requested_historic_value: str
    requested_stop_observations: bool
    retained_row_counts: dict[str, int]
    selected_agency_id: str
    service_files_present: tuple[str, ...]
    source_artifact_filename: str
    source_feed_scope: str
    source_metadata_path: str
    source_system: str
    stop_observations_present: bool
    zip_member_names: tuple[str, ...]
    shape_fallback_used: bool = False
    shape_backfill_cache_hits: int = 0
    shape_backfill_failure_count: int = 0
    shape_backfill_manifest_path: str = ""
    shape_backfill_request_count: int = 0
    shape_backfill_shape_count: int = 0
    shape_backfill_trip_selection_strategy: str = CURRENT_SHAPE_FALLBACK_STRATEGY


@dataclass(frozen=True)
class HistoricSfExtractionResult:
    artifact_path: Path
    metadata_path: Path
    metadata: HistoricSfExtractionMetadata
    reused_existing: bool


def _strip_operator_prefix(value: str, *, operator_id: str) -> str:
    prefix = f"{operator_id}:"
    if value.startswith(prefix):
        return value[len(prefix):]
    return value


def _load_metadata(metadata_path: Path) -> dict[str, Any]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"Historic acquisition metadata file not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    required_fields = (
        "source_system",
        "feed_scope",
        "operator_id",
        "artifact_filename",
        "requested_historic_month",
        "requested_historic_value",
        "requested_stop_observations",
        "stop_observations_present",
    )
    missing_fields = [field for field in required_fields if field not in metadata]
    if missing_fields:
        raise ValueError(
            "Historic acquisition metadata is missing required fields: "
            + ", ".join(missing_fields)
        )
    return metadata


def _coerce_extraction_metadata(payload: Mapping[str, Any]) -> HistoricSfExtractionMetadata:
    defaults: dict[str, Any] = {
        "shape_fallback_used": False,
        "shape_backfill_cache_hits": 0,
        "shape_backfill_failure_count": 0,
        "shape_backfill_manifest_path": "",
        "shape_backfill_request_count": 0,
        "shape_backfill_shape_count": 0,
        "shape_backfill_trip_selection_strategy": CURRENT_SHAPE_FALLBACK_STRATEGY,
    }
    merged = dict(defaults)
    merged.update(payload)
    return HistoricSfExtractionMetadata(**merged)


def _resolve_artifact_path(metadata_path: Path, metadata: Mapping[str, Any]) -> Path:
    artifact_filename = str(metadata["artifact_filename"]).strip()
    if not artifact_filename:
        raise ValueError("Historic acquisition metadata must include artifact_filename.")

    artifact_path = metadata_path.parent / artifact_filename
    if not artifact_path.exists():
        raise FileNotFoundError(f"Historic archive zip not found: {artifact_path}")
    return artifact_path


def _archive_has_shapes_member(artifact_path: Path) -> bool:
    with zipfile.ZipFile(artifact_path, mode="r") as archive:
        return "shapes.txt" in archive.namelist()


def _metadata_has_usable_shapes(payload: Mapping[str, Any]) -> bool:
    retained_row_counts = payload.get("retained_row_counts")
    if isinstance(retained_row_counts, Mapping):
        try:
            return int(retained_row_counts.get("shapes.txt", 0)) > 0
        except (TypeError, ValueError):
            return False
    return False


def _metadata_has_current_shape_fallback_strategy(payload: Mapping[str, Any]) -> bool:
    if not bool(payload.get("shape_fallback_used", False)):
        return True
    return (
        str(payload.get("shape_backfill_trip_selection_strategy", "")).strip()
        == CURRENT_SHAPE_FALLBACK_STRATEGY
    )


def _derived_stem(
    metadata: Mapping[str, Any],
    *,
    selected_agency_id: str,
) -> str:
    source_stem = Path(str(metadata["artifact_filename"])).stem
    return f"{source_stem}_{selected_agency_id}_only"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _stream_filter_member(
    source_archive: zipfile.ZipFile,
    destination_archive: zipfile.ZipFile,
    member_name: str,
    *,
    keep_row: Any,
) -> int:
    if member_name not in source_archive.namelist():
        return 0

    retained_row_count = 0
    with source_archive.open(member_name, mode="r") as source_raw:
        with destination_archive.open(member_name, mode="w") as destination_raw:
            source_text = TextIOWrapper(source_raw, encoding="utf-8", newline="")
            destination_text = TextIOWrapper(destination_raw, encoding="utf-8", newline="")
            reader = csv.DictReader(source_text)
            if reader.fieldnames is None:
                raise ValueError(f"{member_name} has no header row.")

            writer = csv.DictWriter(
                destination_text,
                fieldnames=reader.fieldnames,
                lineterminator="\n",
            )
            writer.writeheader()
            for row in reader:
                if keep_row(row):
                    writer.writerow(row)
                    retained_row_count += 1
            destination_text.flush()
    return retained_row_count


def _collect_retained_shape_rows(
    archive: zipfile.ZipFile,
    *,
    shape_ids: set[str],
) -> tuple[list[dict[str, str]], list[str], set[str]]:
    default_fieldnames = [
        "shape_id",
        "shape_pt_lat",
        "shape_pt_lon",
        "shape_pt_sequence",
        "shape_dist_traveled",
    ]
    if "shapes.txt" not in archive.namelist():
        return [], default_fieldnames, set()

    retained_rows: list[dict[str, str]] = []
    retained_shape_ids: set[str] = set()
    with archive.open("shapes.txt", mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError("shapes.txt has no header row.")
        fieldnames = list(reader.fieldnames)
        for fieldname in default_fieldnames:
            if fieldname not in fieldnames:
                fieldnames.append(fieldname)
        for row in reader:
            shape_id = (row.get("shape_id") or "").strip()
            if shape_id not in shape_ids:
                continue
            retained_rows.append({key: (value or "").strip() for key, value in row.items()})
            retained_shape_ids.add(shape_id)
    return retained_rows, fieldnames, retained_shape_ids


def _write_member_rows(
    destination_archive: zipfile.ZipFile,
    member_name: str,
    *,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> int:
    with destination_archive.open(member_name, mode="w") as destination_raw:
        destination_text = TextIOWrapper(destination_raw, encoding="utf-8", newline="")
        writer = csv.DictWriter(
            destination_text,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        destination_text.flush()
    return len(rows)


def _read_selected_routes(
    archive: zipfile.ZipFile,
    *,
    selected_agency_id: str,
) -> tuple[set[str], int]:
    route_ids: set[str] = set()
    retained_row_count = 0
    with archive.open("routes.txt", mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError("routes.txt has no header row.")

        for row in reader:
            if (row.get("agency_id") or "").strip() != selected_agency_id:
                continue
            route_id = (row.get("route_id") or "").strip()
            if not route_id:
                continue
            route_ids.add(route_id)
            retained_row_count += 1
    if not route_ids:
        raise ValueError(
            f"No routes found for agency_id={selected_agency_id!r} in the historic archive."
        )
    return route_ids, retained_row_count


def _read_selected_trips(
    archive: zipfile.ZipFile,
    *,
    selected_agency_id: str,
    route_ids: set[str],
) -> tuple[
    list[dict[str, str]],
    list[str],
    set[str],
    set[str],
    set[str],
    dict[str, str],
    dict[str, tuple[str, str, str]],
    int,
]:
    default_fieldnames = [
        "route_id",
        "service_id",
        "trip_id",
        "trip_headsign",
        "direction_id",
        "shape_id",
    ]
    trip_ids: set[str] = set()
    service_ids: set[str] = set()
    shape_ids: set[str] = set()
    representative_trip_ids_by_shape_id: dict[str, str] = {}
    lookup_keys_by_shape_id: dict[str, tuple[str, str, str]] = {}
    retained_rows: list[dict[str, str]] = []
    retained_row_count = 0
    with archive.open("trips.txt", mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError("trips.txt has no header row.")
        fieldnames = list(reader.fieldnames)
        for fieldname in default_fieldnames:
            if fieldname not in fieldnames:
                fieldnames.append(fieldname)

        for row in reader:
            route_id = (row.get("route_id") or "").strip()
            if route_id not in route_ids:
                continue

            trip_id = (row.get("trip_id") or "").strip()
            service_id = (row.get("service_id") or "").strip()
            shape_id = (row.get("shape_id") or "").strip()
            direction_id = (row.get("direction_id") or "").strip()
            trip_headsign = (row.get("trip_headsign") or "").strip()
            normalized_route_id = _strip_operator_prefix(route_id, operator_id=selected_agency_id)
            lookup_key = (normalized_route_id, direction_id, trip_headsign)
            normalized_row = {key: (value or "").strip() for key, value in row.items()}
            if trip_id:
                trip_ids.add(trip_id)
            if service_id:
                service_ids.add(service_id)
            if not shape_id and trip_id:
                normalized_shapes_trip_id = normalize_trip_id_for_shapes_api(
                    trip_id,
                    operator_id=selected_agency_id,
                )
                shape_id = f"{selected_agency_id}:shape_api:{normalized_shapes_trip_id}"
                normalized_row["shape_id"] = shape_id
            if shape_id:
                shape_ids.add(shape_id)
                representative_trip_ids_by_shape_id.setdefault(shape_id, trip_id)
                lookup_keys_by_shape_id.setdefault(shape_id, lookup_key)
            retained_rows.append(normalized_row)
            retained_row_count += 1

    if not trip_ids:
        raise ValueError("No trips remained after filtering the historic archive to selected routes.")
    return (
        retained_rows,
        fieldnames,
        trip_ids,
        service_ids,
        shape_ids,
        representative_trip_ids_by_shape_id,
        lookup_keys_by_shape_id,
        retained_row_count,
    )


def _read_active_shape_fallback_data(
    *,
    metadata_path: Path,
    selected_agency_id: str,
) -> tuple[
    dict[tuple[str, str, str], list[tuple[str, str]]],
    dict[tuple[str, str], list[tuple[str, str]]],
    dict[tuple[str, str, str, str], list[tuple[str, str]]],
    dict[str, str],
    dict[str, list[dict[str, str]]],
]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    artifact_path = _resolve_artifact_path(metadata_path, metadata)
    by_route_direction_headsign: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
    by_route_direction: dict[tuple[str, str], list[tuple[str, str]]] = {}
    by_lookup_pattern: dict[tuple[str, str, str, str], list[tuple[str, str]]] = {}
    shape_rows_by_shape_id: dict[str, list[dict[str, str]]] = {}
    trip_metadata_by_trip_id: dict[str, tuple[str, str, str, str]] = {}

    with zipfile.ZipFile(artifact_path, mode="r") as archive:
        with archive.open("trips.txt", mode="r") as raw_handle:
            reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
            if reader.fieldnames is None:
                raise ValueError("Active trips.txt has no header row.")

            for row in reader:
                route_id = (row.get("route_id") or "").strip()
                trip_id = (row.get("trip_id") or "").strip()
                direction_id = (row.get("direction_id") or "").strip()
                trip_headsign = (row.get("trip_headsign") or "").strip()
                shape_id = (row.get("shape_id") or "").strip()
                if not route_id or not trip_id:
                    continue
                normalized_route_id = _strip_operator_prefix(route_id, operator_id=selected_agency_id)
                headsign_key = (normalized_route_id, direction_id, trip_headsign)
                route_direction_key = (normalized_route_id, direction_id)
                by_route_direction_headsign.setdefault(headsign_key, [])
                candidate = (trip_id, shape_id)
                if candidate not in by_route_direction_headsign[headsign_key]:
                    by_route_direction_headsign[headsign_key].append(candidate)
                by_route_direction.setdefault(route_direction_key, [])
                if candidate not in by_route_direction[route_direction_key]:
                    by_route_direction[route_direction_key].append(candidate)
                trip_metadata_by_trip_id[trip_id] = (
                    normalized_route_id,
                    direction_id,
                    trip_headsign,
                    shape_id,
                )

        with archive.open("stop_times.txt", mode="r") as raw_handle:
            reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
            if reader.fieldnames is None:
                raise ValueError("Active stop_times.txt has no header row.")
            stop_pattern_values_by_trip_id: dict[str, list[str]] = {}
            for row in reader:
                trip_id = (row.get("trip_id") or "").strip()
                if trip_id not in trip_metadata_by_trip_id:
                    continue
                stop_id = (row.get("stop_id") or "").strip()
                stop_sequence = (row.get("stop_sequence") or "").strip()
                stop_pattern_values_by_trip_id.setdefault(trip_id, []).append(
                    f"{stop_sequence}:{stop_id}"
                )
            for trip_id, pattern_values in stop_pattern_values_by_trip_id.items():
                route_id, direction_id, trip_headsign, shape_id = trip_metadata_by_trip_id[trip_id]
                stop_pattern_key = hashlib.sha256(
                    "\n".join(pattern_values).encode("utf-8")
                ).hexdigest()[:16]
                lookup_pattern_key = (
                    route_id,
                    direction_id,
                    trip_headsign,
                    stop_pattern_key,
                )
                by_lookup_pattern.setdefault(lookup_pattern_key, [])
                candidate = (trip_id, shape_id)
                if candidate not in by_lookup_pattern[lookup_pattern_key]:
                    by_lookup_pattern[lookup_pattern_key].append(candidate)

        with archive.open("shapes.txt", mode="r") as raw_handle:
            reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
            if reader.fieldnames is None:
                raise ValueError("Active shapes.txt has no header row.")
            for row in reader:
                shape_id = (row.get("shape_id") or "").strip()
                if not shape_id:
                    continue
                shape_rows_by_shape_id.setdefault(shape_id, []).append(
                    {key: (value or "").strip() for key, value in row.items()}
                )

    active_shape_id_by_trip_id = {
        trip_id: shape_id
        for trip_id, (_route_id, _direction_id, _trip_headsign, shape_id) in trip_metadata_by_trip_id.items()
        if shape_id
    }
    return (
        by_route_direction_headsign,
        by_route_direction,
        by_lookup_pattern,
        active_shape_id_by_trip_id,
        shape_rows_by_shape_id,
    )


def _select_unique_active_shape_id(
    candidates: list[tuple[str, str]],
) -> str | None:
    unique_shape_ids = {
        shape_id
        for _trip_id, shape_id in candidates
        if shape_id
    }
    if len(unique_shape_ids) == 1:
        return next(iter(unique_shape_ids))
    return None


def _build_unique_active_shape_lookup(
    by_route_direction_headsign: Mapping[tuple[str, str, str], list[tuple[str, str]]],
) -> dict[tuple[str, str, str], str]:
    resolved: dict[tuple[str, str, str], str] = {}
    for key, candidates in by_route_direction_headsign.items():
        unique_shape_id = _select_unique_active_shape_id(list(candidates))
        if unique_shape_id is not None:
            resolved[key] = unique_shape_id
    return resolved


def _build_unique_active_shape_lookup_by_pattern(
    by_lookup_pattern: Mapping[tuple[str, str, str, str], list[tuple[str, str]]],
) -> dict[tuple[str, str, str, str], str]:
    resolved: dict[tuple[str, str, str, str], str] = {}
    for key, candidates in by_lookup_pattern.items():
        unique_shape_id = _select_unique_active_shape_id(list(candidates))
        if unique_shape_id is not None:
            resolved[key] = unique_shape_id
    return resolved


def _build_shape_pattern_id(
    *,
    selected_agency_id: str,
    route_id: str,
    direction_id: str,
    trip_headsign: str,
    stop_pattern_key: str,
) -> str:
    digest = hashlib.sha256(
        f"{route_id}\0{direction_id}\0{trip_headsign}\0{stop_pattern_key}".encode("utf-8")
    ).hexdigest()[:16]
    return f"{selected_agency_id}:shape_pattern:{digest}"


def _normalize_synthetic_shape_targets(
    retained_trip_rows: list[dict[str, str]],
    *,
    selected_agency_id: str,
    unique_active_shape_by_lookup_key: Mapping[tuple[str, str, str], str],
    unique_active_shape_by_lookup_pattern_key: Mapping[tuple[str, str, str, str], str],
    stop_pattern_key_by_trip_id: Mapping[str, str],
) -> tuple[set[str], dict[str, str], dict[str, tuple[str, str, str]]]:
    shape_ids: set[str] = set()
    representative_trip_ids_by_shape_id: dict[str, str] = {}
    lookup_keys_by_shape_id: dict[str, tuple[str, str, str]] = {}

    for row in retained_trip_rows:
        route_id = (row.get("route_id") or "").strip()
        direction_id = (row.get("direction_id") or "").strip()
        trip_headsign = (row.get("trip_headsign") or "").strip()
        trip_id = (row.get("trip_id") or "").strip()
        shape_id = (row.get("shape_id") or "").strip()
        lookup_key = (_strip_operator_prefix(route_id, operator_id=selected_agency_id), direction_id, trip_headsign)

        if shape_id.startswith(f"{selected_agency_id}:shape_api:"):
            stop_pattern_key = stop_pattern_key_by_trip_id.get(trip_id, "")
            unique_active_shape_id = None
            if stop_pattern_key:
                unique_active_shape_id = unique_active_shape_by_lookup_pattern_key.get(
                    (
                        lookup_key[0],
                        lookup_key[1],
                        lookup_key[2],
                        stop_pattern_key,
                    )
                )
            if unique_active_shape_id is None and not stop_pattern_key:
                unique_active_shape_id = unique_active_shape_by_lookup_key.get(lookup_key)
            if unique_active_shape_id:
                shape_id = f"{selected_agency_id}:active_shape:{unique_active_shape_id}"
            elif stop_pattern_key:
                shape_id = _build_shape_pattern_id(
                    selected_agency_id=selected_agency_id,
                    route_id=route_id,
                    direction_id=direction_id,
                    trip_headsign=trip_headsign,
                    stop_pattern_key=stop_pattern_key,
                )
            row["shape_id"] = shape_id

        if shape_id:
            shape_ids.add(shape_id)
            representative_trip_ids_by_shape_id.setdefault(shape_id, trip_id)
            lookup_keys_by_shape_id.setdefault(shape_id, lookup_key)

    return shape_ids, representative_trip_ids_by_shape_id, lookup_keys_by_shape_id


def _read_selected_stop_ids(
    archive: zipfile.ZipFile,
    *,
    trip_ids: set[str],
) -> tuple[set[str], int, dict[str, str]]:
    stop_ids: set[str] = set()
    retained_row_count = 0
    stop_pattern_values_by_trip_id: dict[str, list[str]] = {}
    with archive.open("stop_times.txt", mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError("stop_times.txt has no header row.")

        for row in reader:
            trip_id = (row.get("trip_id") or "").strip()
            if trip_id not in trip_ids:
                continue
            stop_id = (row.get("stop_id") or "").strip()
            stop_sequence = (row.get("stop_sequence") or "").strip()
            if stop_id:
                stop_ids.add(stop_id)
                stop_pattern_values_by_trip_id.setdefault(trip_id, []).append(
                    f"{stop_sequence}:{stop_id}"
                )
            retained_row_count += 1

    stop_pattern_key_by_trip_id: dict[str, str] = {}
    for trip_id, pattern_values in stop_pattern_values_by_trip_id.items():
        stop_pattern_key_by_trip_id[trip_id] = hashlib.sha256(
            "\n".join(pattern_values).encode("utf-8")
        ).hexdigest()[:16]

    return stop_ids, retained_row_count, stop_pattern_key_by_trip_id


def _build_metadata(
    *,
    metadata_path: Path,
    source_metadata: Mapping[str, Any],
    artifact_path: Path,
    retained_row_counts: Mapping[str, int],
    selected_agency_id: str,
    shape_fallback_metadata: Mapping[str, Any],
    zip_member_names: tuple[str, ...],
) -> HistoricSfExtractionMetadata:
    service_files_present = tuple(
        name for name in OPTIONAL_GTFS_FILES if name in zip_member_names
    )
    return HistoricSfExtractionMetadata(
        artifact_filename=artifact_path.name,
        artifact_sha256=_hash_file(artifact_path),
        artifact_size_bytes=artifact_path.stat().st_size,
        derived_at=datetime.now(tz=UTC).isoformat(),
        feed_scope=DERIVED_FEED_SCOPE,
        operator_id=selected_agency_id,
        requested_historic_month=str(source_metadata["requested_historic_month"]),
        requested_historic_value=str(source_metadata["requested_historic_value"]),
        requested_stop_observations=bool(source_metadata["requested_stop_observations"]),
        retained_row_counts=dict(retained_row_counts),
        selected_agency_id=selected_agency_id,
        service_files_present=service_files_present,
        source_artifact_filename=str(source_metadata["artifact_filename"]),
        source_feed_scope=str(source_metadata["feed_scope"]),
        source_metadata_path=str(metadata_path),
        source_system=str(source_metadata["source_system"]),
        shape_fallback_used=bool(shape_fallback_metadata.get("shape_fallback_used", False)),
        shape_backfill_cache_hits=int(shape_fallback_metadata.get("shape_backfill_cache_hits", 0)),
        shape_backfill_failure_count=int(shape_fallback_metadata.get("shape_backfill_failure_count", 0)),
        shape_backfill_manifest_path=str(shape_fallback_metadata.get("shape_backfill_manifest_path", "")),
        shape_backfill_request_count=int(shape_fallback_metadata.get("shape_backfill_request_count", 0)),
        shape_backfill_shape_count=int(shape_fallback_metadata.get("shape_backfill_shape_count", 0)),
        shape_backfill_trip_selection_strategy=str(
            shape_fallback_metadata.get(
                "shape_backfill_trip_selection_strategy",
                CURRENT_SHAPE_FALLBACK_STRATEGY,
            )
        ),
        stop_observations_present=STOP_OBSERVATIONS_FILENAME in zip_member_names,
        zip_member_names=zip_member_names,
    )


def extract_sf_historic_archive(
    *,
    metadata_path: Path,
    selected_agency_id: str = DEFAULT_SELECTED_AGENCY_ID,
    acquisitions_root: Path = DEFAULT_DERIVED_ACQUISITIONS_ROOT,
    api_key: str | None = None,
    shapes_cache_root: Path = DEFAULT_SHAPES_CACHE_ROOT,
    active_metadata_path: Path | None = None,
) -> HistoricSfExtractionResult:
    source_metadata = _load_metadata(metadata_path)
    if (
        str(source_metadata.get("feed_scope")) == DERIVED_FEED_SCOPE
        and str(source_metadata.get("selected_agency_id")) == selected_agency_id
    ):
        artifact_path = _resolve_artifact_path(metadata_path, source_metadata)
        if not (
            _archive_has_shapes_member(artifact_path)
            and _metadata_has_usable_shapes(source_metadata)
            and _metadata_has_current_shape_fallback_strategy(source_metadata)
        ):
            source_metadata = dict(source_metadata)
        else:
            return HistoricSfExtractionResult(
                artifact_path=artifact_path,
                metadata_path=metadata_path,
                metadata=_coerce_extraction_metadata(source_metadata),
                reused_existing=True,
            )

    source_artifact_path = _resolve_artifact_path(metadata_path, source_metadata)
    derived_stem = _derived_stem(source_metadata, selected_agency_id=selected_agency_id)
    acquisitions_root.mkdir(parents=True, exist_ok=True)
    artifact_path = acquisitions_root / f"{derived_stem}.zip"
    metadata_output_path = acquisitions_root / f"{derived_stem}.json"

    if artifact_path.exists() and metadata_output_path.exists():
        existing_metadata_payload = json.loads(metadata_output_path.read_text(encoding="utf-8"))
        if (
            _archive_has_shapes_member(artifact_path)
            and _metadata_has_usable_shapes(existing_metadata_payload)
            and _metadata_has_current_shape_fallback_strategy(existing_metadata_payload)
        ):
            existing_metadata = _coerce_extraction_metadata(existing_metadata_payload)
            return HistoricSfExtractionResult(
                artifact_path=artifact_path,
                metadata_path=metadata_output_path,
                metadata=existing_metadata,
                reused_existing=True,
            )

    retained_row_counts: dict[str, int] = {}
    shape_fallback_metadata: dict[str, Any] = {
        "shape_fallback_used": False,
        "shape_backfill_cache_hits": 0,
        "shape_backfill_failure_count": 0,
        "shape_backfill_manifest_path": "",
        "shape_backfill_request_count": 0,
        "shape_backfill_shape_count": 0,
        "shape_backfill_trip_selection_strategy": CURRENT_SHAPE_FALLBACK_STRATEGY,
    }
    with zipfile.ZipFile(source_artifact_path, mode="r") as source_archive:
        active_by_route_direction_headsign: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
        active_by_route_direction: dict[tuple[str, str], list[tuple[str, str]]] = {}
        active_by_lookup_pattern: dict[tuple[str, str, str, str], list[tuple[str, str]]] = {}
        active_shape_id_by_trip_id: dict[str, str] = {}
        active_shape_rows_by_shape_id: dict[str, list[dict[str, str]]] = {}
        unique_active_shape_by_lookup_key: dict[tuple[str, str, str], str] = {}
        unique_active_shape_by_lookup_pattern_key: dict[tuple[str, str, str, str], str] = {}
        if active_metadata_path is not None:
            (
                active_by_route_direction_headsign,
                active_by_route_direction,
                active_by_lookup_pattern,
                active_shape_id_by_trip_id,
                active_shape_rows_by_shape_id,
            ) = _read_active_shape_fallback_data(
                metadata_path=active_metadata_path,
                selected_agency_id=selected_agency_id,
            )
            unique_active_shape_by_lookup_key = _build_unique_active_shape_lookup(
                active_by_route_direction_headsign
            )
            unique_active_shape_by_lookup_pattern_key = _build_unique_active_shape_lookup_by_pattern(
                active_by_lookup_pattern
            )
        route_ids, retained_row_counts["routes.txt"] = _read_selected_routes(
            source_archive,
            selected_agency_id=selected_agency_id,
        )
        (
            retained_trip_rows,
            trip_fieldnames,
            trip_ids,
            service_ids,
            shape_ids,
            representative_trip_ids_by_shape_id,
            lookup_keys_by_shape_id,
            retained_row_counts["trips.txt"],
        ) = _read_selected_trips(
            source_archive,
            selected_agency_id=selected_agency_id,
            route_ids=route_ids,
        )
        stop_ids, retained_row_counts["stop_times.txt"], stop_pattern_key_by_trip_id = _read_selected_stop_ids(
            source_archive,
            trip_ids=trip_ids,
        )
        (
            shape_ids,
            representative_trip_ids_by_shape_id,
            lookup_keys_by_shape_id,
        ) = _normalize_synthetic_shape_targets(
            retained_trip_rows,
            selected_agency_id=selected_agency_id,
            unique_active_shape_by_lookup_key=unique_active_shape_by_lookup_key,
            unique_active_shape_by_lookup_pattern_key=unique_active_shape_by_lookup_pattern_key,
            stop_pattern_key_by_trip_id=stop_pattern_key_by_trip_id,
        )
        retained_shape_rows, shape_fieldnames, retained_shape_ids = _collect_retained_shape_rows(
            source_archive,
            shape_ids=shape_ids,
        )
        missing_shape_ids = sorted(shape_ids - retained_shape_ids)

        if missing_shape_ids:
            if api_key is None:
                api_key = get_511_api_key()
            resolved_active_shape_ids: list[str] = []
            shape_id_to_trip_candidates: dict[str, list[str]] = {}
            for shape_id in missing_shape_ids:
                candidate_trip_ids: list[str] = []
                representative_trip_id = representative_trip_ids_by_shape_id[shape_id]
                if representative_trip_id:
                    candidate_trip_ids.append(representative_trip_id)
                route_direction_headsign_key = lookup_keys_by_shape_id.get(shape_id)
                if route_direction_headsign_key is not None:
                    stop_pattern_key = stop_pattern_key_by_trip_id.get(representative_trip_id, "")
                    lookup_pattern_key = None
                    exact_active_shape_id = None
                    exact_active_candidates: list[tuple[str, str]] = []
                    normalized_representative_trip_id = normalize_trip_id_for_shapes_api(
                        representative_trip_id,
                        operator_id=selected_agency_id,
                    )
                    exact_trip_active_shape_id = active_shape_id_by_trip_id.get(
                        normalized_representative_trip_id
                    )
                    if exact_trip_active_shape_id is not None:
                        active_shape_rows = active_shape_rows_by_shape_id.get(
                            exact_trip_active_shape_id,
                            [],
                        )
                        if active_shape_rows:
                            retained_shape_rows.extend(
                                [
                                    {**row, "shape_id": shape_id}
                                    for row in active_shape_rows
                                ]
                            )
                            resolved_active_shape_ids.append(shape_id)
                            continue
                    if stop_pattern_key:
                        lookup_pattern_key = (
                            route_direction_headsign_key[0],
                            route_direction_headsign_key[1],
                            route_direction_headsign_key[2],
                            stop_pattern_key,
                        )
                        exact_active_shape_id = unique_active_shape_by_lookup_pattern_key.get(
                            lookup_pattern_key
                        )
                        exact_active_candidates = list(
                            active_by_lookup_pattern.get(lookup_pattern_key, [])
                        )
                    elif shape_id.startswith(f"{selected_agency_id}:active_shape:"):
                        exact_active_shape_id = unique_active_shape_by_lookup_key.get(
                            route_direction_headsign_key
                        )
                    if exact_active_shape_id is not None:
                        active_shape_rows = active_shape_rows_by_shape_id.get(exact_active_shape_id, [])
                        if active_shape_rows:
                            if shape_id.startswith(f"{selected_agency_id}:active_shape:"):
                                retained_shape_rows.extend(
                                    [
                                        {**row, "shape_id": shape_id}
                                        for row in active_shape_rows
                                    ]
                                )
                                resolved_active_shape_ids.append(shape_id)
                                continue
                    seen_active_shape_ids: set[str] = set()
                    seen_active_trip_ids: set[str] = set()
                    for active_trip_id, active_shape_id in exact_active_candidates:
                        if active_trip_id:
                            if active_shape_id:
                                if active_shape_id in seen_active_shape_ids:
                                    continue
                                seen_active_shape_ids.add(active_shape_id)
                            elif active_trip_id in seen_active_trip_ids:
                                continue
                            seen_active_trip_ids.add(active_trip_id)
                            candidate_trip_ids.append(active_trip_id)
                    if not exact_active_candidates:
                        same_headsign_candidates = list(
                            active_by_route_direction_headsign.get(route_direction_headsign_key, [])
                        )
                        for active_trip_id, active_shape_id in same_headsign_candidates:
                            if active_trip_id:
                                if active_shape_id:
                                    if active_shape_id in seen_active_shape_ids:
                                        continue
                                    seen_active_shape_ids.add(active_shape_id)
                                elif active_trip_id in seen_active_trip_ids:
                                    continue
                                seen_active_trip_ids.add(active_trip_id)
                                candidate_trip_ids.append(active_trip_id)
                deduped_candidate_trip_ids: list[str] = []
                for candidate_trip_id in candidate_trip_ids:
                    if candidate_trip_id and candidate_trip_id not in deduped_candidate_trip_ids:
                        deduped_candidate_trip_ids.append(candidate_trip_id)
                shape_id_to_trip_candidates[shape_id] = deduped_candidate_trip_ids
            shape_fallback_manifest_payload: dict[str, Any] = {
                "source_archive_lacked_shapes_txt": "shapes.txt" not in source_archive.namelist(),
                "shape_fallback_used": True,
                "shape_backfill_trip_selection_strategy": CURRENT_SHAPE_FALLBACK_STRATEGY,
                "missing_shape_ids": missing_shape_ids,
                "resolved_from_active_archive_shape_count": len(resolved_active_shape_ids),
                "written_at": datetime.now(tz=UTC).isoformat(),
            }
            if shape_id_to_trip_candidates:
                backfill_result = backfill_missing_shapes(
                    shape_id_to_trip_candidates,
                    api_key=api_key,
                    operator_id=selected_agency_id,
                    cache_root=shapes_cache_root,
                )
                if backfill_result.failure_shape_ids:
                    unresolved = ", ".join(backfill_result.failure_shape_ids)
                    raise RuntimeError(
                        "Failed to backfill required Shapes API geometries for shape_ids: "
                        f"{unresolved}"
                    )

                retained_shape_rows.extend(backfill_result.shape_rows)
                shape_fallback_manifest_payload.update(
                    {
                        "shape_backfill_cache_hits": backfill_result.cache_hit_count,
                        "shape_backfill_failure_count": len(backfill_result.failure_shape_ids),
                        "shape_backfill_request_count": backfill_result.request_count,
                        "shape_backfill_shape_count": (
                            len(resolved_active_shape_ids) + backfill_result.successful_shape_count
                        ),
                        "artifacts": [
                            {
                                **asdict(artifact),
                                "cache_path": str(artifact.cache_path),
                            }
                            for artifact in backfill_result.artifacts
                        ],
                    }
                )
            else:
                shape_fallback_manifest_payload.update(
                    {
                        "shape_backfill_cache_hits": 0,
                        "shape_backfill_failure_count": 0,
                        "shape_backfill_request_count": 0,
                        "shape_backfill_shape_count": len(resolved_active_shape_ids),
                        "artifacts": [],
                    }
                )
            shape_fallback_manifest_path = acquisitions_root / f"{derived_stem}_shape_backfill.json"
            _write_json(shape_fallback_manifest_path, shape_fallback_manifest_payload)
            shape_fallback_metadata = {
                "shape_fallback_used": True,
                "shape_backfill_cache_hits": int(shape_fallback_manifest_payload["shape_backfill_cache_hits"]),
                "shape_backfill_failure_count": int(shape_fallback_manifest_payload["shape_backfill_failure_count"]),
                "shape_backfill_manifest_path": str(shape_fallback_manifest_path),
                "shape_backfill_request_count": int(shape_fallback_manifest_payload["shape_backfill_request_count"]),
                "shape_backfill_shape_count": int(shape_fallback_manifest_payload["shape_backfill_shape_count"]),
                "shape_backfill_trip_selection_strategy": CURRENT_SHAPE_FALLBACK_STRATEGY,
            }

        with zipfile.ZipFile(
            artifact_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as destination_archive:
            retained_row_counts["routes.txt"] = _stream_filter_member(
                source_archive,
                destination_archive,
                "routes.txt",
                keep_row=lambda row: (row.get("route_id") or "").strip() in route_ids,
            )
            retained_row_counts["trips.txt"] = _write_member_rows(
                destination_archive,
                "trips.txt",
                fieldnames=trip_fieldnames,
                rows=retained_trip_rows,
            )
            retained_row_counts["stop_times.txt"] = _stream_filter_member(
                source_archive,
                destination_archive,
                "stop_times.txt",
                keep_row=lambda row: (row.get("trip_id") or "").strip() in trip_ids,
            )
            retained_row_counts["stops.txt"] = _stream_filter_member(
                source_archive,
                destination_archive,
                "stops.txt",
                keep_row=lambda row: (row.get("stop_id") or "").strip() in stop_ids,
            )
            retained_row_counts["shapes.txt"] = _write_member_rows(
                destination_archive,
                "shapes.txt",
                fieldnames=shape_fieldnames,
                rows=retained_shape_rows,
            )

            for service_file in OPTIONAL_GTFS_FILES:
                if service_file not in source_archive.namelist():
                    continue
                retained_row_counts[service_file] = _stream_filter_member(
                    source_archive,
                    destination_archive,
                    service_file,
                    keep_row=lambda row, service_ids=service_ids: (
                        (row.get("service_id") or "").strip() in service_ids
                    ),
                )

            if bool(source_metadata["requested_stop_observations"]) and (
                STOP_OBSERVATIONS_FILENAME in source_archive.namelist()
            ):
                prefix = f"{selected_agency_id}:"
                retained_row_counts[STOP_OBSERVATIONS_FILENAME] = _stream_filter_member(
                    source_archive,
                    destination_archive,
                    STOP_OBSERVATIONS_FILENAME,
                    keep_row=lambda row: (
                        (row.get("agency_id") or "").strip() == selected_agency_id
                        or (row.get("trip_id") or "").strip() in trip_ids
                        or (row.get("route_id") or "").strip() in route_ids
                        or (row.get("trip_id") or "").strip().startswith(prefix)
                        or (row.get("route_id") or "").strip().startswith(prefix)
                    ),
                )

    with zipfile.ZipFile(artifact_path, mode="r") as derived_archive:
        zip_member_names = tuple(sorted(derived_archive.namelist()))

    metadata = _build_metadata(
        metadata_path=metadata_path,
        source_metadata=source_metadata,
        artifact_path=artifact_path,
        retained_row_counts=retained_row_counts,
        selected_agency_id=selected_agency_id,
        shape_fallback_metadata=shape_fallback_metadata,
        zip_member_names=zip_member_names,
    )
    _write_json(metadata_output_path, asdict(metadata))
    return HistoricSfExtractionResult(
        artifact_path=artifact_path,
        metadata_path=metadata_output_path,
        metadata=metadata,
        reused_existing=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-path",
        type=Path,
        required=True,
        help="Path to the fetched historic RG acquisition JSON sidecar.",
    )
    parser.add_argument(
        "--agency-id",
        default=DEFAULT_SELECTED_AGENCY_ID,
        help="Agency id to isolate from the historic regional archive. Defaults to SF.",
    )
    parser.add_argument(
        "--acquisitions-root",
        type=Path,
        default=DEFAULT_DERIVED_ACQUISITIONS_ROOT,
        help="Directory where the derived SF-only archive artifacts should be written.",
    )
    args = parser.parse_args()

    result = extract_sf_historic_archive(
        metadata_path=args.metadata_path,
        selected_agency_id=args.agency_id,
        acquisitions_root=args.acquisitions_root,
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["artifact_path", "metadata_path", "reused_existing"])
    writer.writerow([result.artifact_path, result.metadata_path, result.reused_existing])
    print(output.getvalue().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
