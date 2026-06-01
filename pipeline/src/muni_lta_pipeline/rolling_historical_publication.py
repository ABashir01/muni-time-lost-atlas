"""Maintain a rolling historical publication window for the live app database."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
import hashlib
import json
import os
from io import TextIOWrapper
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable, Mapping
import zipfile

from muni_lta_pipeline.active_gtfs_fetch import fetch_active_gtfs_archive, get_511_api_key
from muni_lta_pipeline.gtfs_static_fixture_ingest import REPO_ROOT
from muni_lta_pipeline.historic_rg_feed_fetch import (
    STOP_OBSERVATIONS_FILENAME,
    HistoricAvailabilityResult,
    check_historic_rg_gtfs_archive_availability,
    fetch_historic_rg_gtfs_archive,
    validate_historic_month,
)
from muni_lta_pipeline.historic_rg_sf_extract import extract_sf_historic_archive
from muni_lta_pipeline.real_dataset_cutover import (
    RealDatasetCutoverResult,
    materialize_prepared_historic_publication,
)


DEFAULT_HISTORIC_AGENCY_ID = "SF"
DEFAULT_ROLLING_WINDOW_MONTHS = 3
DEFAULT_PUBLICATION_ROOT = Path(
    os.environ.get(
        "PUBLICATION_ROOT",
        str(REPO_ROOT / "artifacts" / "publications" / "b7_rolling_historical_publication"),
    )
)
DEFAULT_PUBLICATION_CUTOVER_ROOT = DEFAULT_PUBLICATION_ROOT / "cutovers"
DEFAULT_PUBLICATION_ACQUISITIONS_ROOT = DEFAULT_PUBLICATION_ROOT / "acquisitions"
DEFAULT_ACTIVE_PUBLICATION_ACQUISITIONS_ROOT = (
    DEFAULT_PUBLICATION_ACQUISITIONS_ROOT / "operator_active"
)
DEFAULT_HISTORIC_PUBLICATION_ACQUISITIONS_ROOT = (
    DEFAULT_PUBLICATION_ACQUISITIONS_ROOT / "regional_historic"
)
DEFAULT_DERIVED_PUBLICATION_ACQUISITIONS_ROOT = (
    DEFAULT_PUBLICATION_ACQUISITIONS_ROOT / "regional_historic_sf"
)
DEFAULT_COMBINED_ACQUISITIONS_ROOT = (
    DEFAULT_PUBLICATION_ACQUISITIONS_ROOT / "regional_historic_sf_publication"
)
DERIVED_PUBLICATION_FEED_SCOPE = "regional_historic_sf_publication"
PUBLICATION_KIND = "rolling_historical_window"


@dataclass(frozen=True)
class RollingPublicationResult:
    action: str
    historic_agency_id: str
    latest_available_month: str
    publication_months: tuple[str, ...]
    publication_manifest_path: Path
    latest_publication_manifest_path: Path
    active_metadata_path: Path | None
    combined_metadata_path: Path | None
    cutover_manifest_path: Path | None
    availability_status_code: int
    availability_request_method: str
    published: bool
    route_count_with_metrics: int | None
    map_route_count: int | None
    top_route_ids: tuple[str, ...]


@dataclass(frozen=True)
class CombinedHistoricArchiveResult:
    artifact_path: Path
    metadata_path: Path
    retained_row_counts: dict[str, int]
    publication_months: tuple[str, ...]


def _split_historic_month(historic_month: str) -> tuple[int, int]:
    normalized = validate_historic_month(historic_month)
    year_text, month_text = normalized.split("-", 1)
    return int(year_text), int(month_text)


def _format_historic_month(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def shift_historic_month(historic_month: str, offset_months: int) -> str:
    year, month = _split_historic_month(historic_month)
    zero_based = (year * 12) + (month - 1) + offset_months
    if zero_based < 0:
        raise ValueError("Historic month offset moved before year 0001.")
    shifted_year, shifted_month_index = divmod(zero_based, 12)
    return _format_historic_month(shifted_year, shifted_month_index + 1)


def newest_completed_historic_month(*, current_date: date | None = None) -> str:
    today = current_date or datetime.now().date()
    return shift_historic_month(_format_historic_month(today.year, today.month), -1)


def build_trailing_publication_months(
    latest_historic_month: str,
    *,
    window_months: int = DEFAULT_ROLLING_WINDOW_MONTHS,
) -> tuple[str, ...]:
    if window_months <= 0:
        raise ValueError("window_months must be positive.")
    normalized_latest = validate_historic_month(latest_historic_month)
    months = [
        shift_historic_month(normalized_latest, offset)
        for offset in range(-(window_months - 1), 1)
    ]
    return tuple(months)


def check_newest_available_completed_month(
    *,
    api_key: str,
    current_date: date | None = None,
    timeout_seconds: int = 30,
) -> HistoricAvailabilityResult:
    return check_historic_rg_gtfs_archive_availability(
        api_key=api_key,
        historic_month=newest_completed_historic_month(current_date=current_date),
        include_stop_observations=True,
        timeout_seconds=timeout_seconds,
    )


def _namespace_value(month_token: str, value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    return f"{month_token}__{value}"


def _read_archive_rows(
    archive: zipfile.ZipFile,
    member_name: str,
) -> tuple[list[str], list[dict[str, str]]]:
    if member_name not in archive.namelist():
        return [], []
    with archive.open(member_name, mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError(f"{member_name} has no header row.")
        fieldnames = list(reader.fieldnames)
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    return fieldnames, rows


def _open_archive_reader(
    archive: zipfile.ZipFile,
    member_name: str,
) -> tuple[list[str], csv.DictReader[str], TextIOWrapper] | None:
    if member_name not in archive.namelist():
        return None
    raw_handle = archive.open(member_name, mode="r")
    text_handle = TextIOWrapper(raw_handle, encoding="utf-8", newline="")
    reader = csv.DictReader(text_handle)
    if reader.fieldnames is None:
        text_handle.close()
        raise ValueError(f"{member_name} has no header row.")
    return list(reader.fieldnames), reader, text_handle


def _merge_fieldnames(existing: list[str], incoming: Iterable[str]) -> list[str]:
    merged = list(existing)
    for fieldname in incoming:
        if fieldname not in merged:
            merged.append(fieldname)
    return merged


def _write_rows_to_zip(
    archive: zipfile.ZipFile,
    member_name: str,
    *,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> int:
    with archive.open(member_name, mode="w", force_zip64=True) as raw_handle:
        text_handle = TextIOWrapper(raw_handle, encoding="utf-8", newline="")
        writer = csv.DictWriter(text_handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
        text_handle.flush()
    return len(rows)


def _append_jsonl_row(path: Path, row: Mapping[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), sort_keys=True))
        handle.write("\n")


def _iter_jsonl_rows(path: Path) -> Iterable[dict[str, str]]:
    if not path.exists():
        return ()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            yield json.loads(stripped)


def _write_jsonl_rows_to_zip(
    archive: zipfile.ZipFile,
    member_name: str,
    *,
    fieldnames: list[str],
    spool_path: Path,
) -> int:
    row_count = 0
    with archive.open(member_name, mode="w", force_zip64=True) as raw_handle:
        text_handle = TextIOWrapper(raw_handle, encoding="utf-8", newline="")
        writer = csv.DictWriter(text_handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in _iter_jsonl_rows(spool_path):
            writer.writerow({field: row.get(field, "") for field in fieldnames})
            row_count += 1
        text_handle.flush()
    return row_count


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def combine_historic_month_archives(
    *,
    metadata_paths: Iterable[Path],
    selected_agency_id: str = DEFAULT_HISTORIC_AGENCY_ID,
    combined_acquisitions_root: Path = DEFAULT_COMBINED_ACQUISITIONS_ROOT,
) -> CombinedHistoricArchiveResult:
    ordered_metadata_paths = [Path(path) for path in metadata_paths]
    if not ordered_metadata_paths:
        raise ValueError("At least one historic metadata path is required.")

    publication_months: list[str] = []
    route_fieldnames: list[str] = []
    stop_fieldnames: list[str] = []
    trip_fieldnames: list[str] = []
    stop_time_fieldnames: list[str] = []
    shape_fieldnames: list[str] = []
    stop_observation_fieldnames: list[str] = []
    calendar_fieldnames: list[str] = []
    calendar_dates_fieldnames: list[str] = []

    routes_by_id: dict[str, dict[str, str]] = {}
    stops_by_id: dict[str, dict[str, str]] = {}
    combined_acquisitions_root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="combined_historic_", dir=combined_acquisitions_root) as temp_dir:
        temp_root = Path(temp_dir)
        trip_spool = temp_root / "trips.jsonl"
        stop_time_spool = temp_root / "stop_times.jsonl"
        shape_spool = temp_root / "shapes.jsonl"
        stop_observation_spool = temp_root / "stop_observations.jsonl"
        calendar_spool = temp_root / "calendar.jsonl"
        calendar_dates_spool = temp_root / "calendar_dates.jsonl"
        shape_row_count = 0
        stop_observation_row_count = 0
        calendar_row_count = 0
        calendar_dates_row_count = 0

        for metadata_path in ordered_metadata_paths:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            historic_month = validate_historic_month(str(metadata["requested_historic_month"]))
            publication_months.append(historic_month)
            month_token = historic_month.replace("-", "")
            artifact_path = metadata_path.parent / str(metadata["artifact_filename"])
            if not artifact_path.exists():
                raise FileNotFoundError(f"Historic publication source zip not found: {artifact_path}")

            trip_id_map: dict[str, str] = {}
            service_id_map: dict[str, str] = {}
            shape_id_map: dict[str, str] = {}

            with zipfile.ZipFile(artifact_path, mode="r") as archive:
                current_route_fieldnames, route_rows = _read_archive_rows(archive, "routes.txt")
                route_fieldnames = _merge_fieldnames(route_fieldnames, current_route_fieldnames)
                for row in route_rows:
                    route_id = (row.get("route_id") or "").strip()
                    if route_id:
                        routes_by_id[route_id] = row

                current_stop_fieldnames, stop_rows = _read_archive_rows(archive, "stops.txt")
                stop_fieldnames = _merge_fieldnames(stop_fieldnames, current_stop_fieldnames)
                for row in stop_rows:
                    stop_id = (row.get("stop_id") or "").strip()
                    if stop_id:
                        stops_by_id[stop_id] = row

                trip_reader_bundle = _open_archive_reader(archive, "trips.txt")
                if trip_reader_bundle is None:
                    raise ValueError("trips.txt is required in the historic publication source archive.")
                current_trip_fieldnames, trip_reader, trip_handle = trip_reader_bundle
                try:
                    trip_fieldnames = _merge_fieldnames(trip_fieldnames, current_trip_fieldnames)
                    for row in trip_reader:
                        normalized_row = {key: (value or "").strip() for key, value in row.items()}
                        original_trip_id = (normalized_row.get("trip_id") or "").strip()
                        original_service_id = (normalized_row.get("service_id") or "").strip()
                        original_shape_id = (normalized_row.get("shape_id") or "").strip()
                        namespaced_trip_id = _namespace_value(month_token, original_trip_id)
                        namespaced_service_id = _namespace_value(month_token, original_service_id)
                        namespaced_shape_id = _namespace_value(month_token, original_shape_id)
                        normalized_row["trip_id"] = namespaced_trip_id
                        normalized_row["service_id"] = namespaced_service_id
                        normalized_row["shape_id"] = namespaced_shape_id
                        _append_jsonl_row(trip_spool, normalized_row)
                        if original_trip_id:
                            trip_id_map[original_trip_id] = namespaced_trip_id
                        if original_service_id:
                            service_id_map[original_service_id] = namespaced_service_id
                        if original_shape_id:
                            shape_id_map[original_shape_id] = namespaced_shape_id
                finally:
                    trip_handle.close()

                stop_time_reader_bundle = _open_archive_reader(archive, "stop_times.txt")
                if stop_time_reader_bundle is None:
                    raise ValueError("stop_times.txt is required in the historic publication source archive.")
                current_stop_time_fieldnames, stop_time_reader, stop_time_handle = stop_time_reader_bundle
                try:
                    stop_time_fieldnames = _merge_fieldnames(stop_time_fieldnames, current_stop_time_fieldnames)
                    for row in stop_time_reader:
                        normalized_row = {key: (value or "").strip() for key, value in row.items()}
                        original_trip_id = (normalized_row.get("trip_id") or "").strip()
                        if original_trip_id not in trip_id_map:
                            continue
                        normalized_row["trip_id"] = trip_id_map[original_trip_id]
                        _append_jsonl_row(stop_time_spool, normalized_row)
                finally:
                    stop_time_handle.close()

                shape_reader_bundle = _open_archive_reader(archive, "shapes.txt")
                if shape_reader_bundle is None:
                    raise ValueError("shapes.txt is required in the historic publication source archive.")
                current_shape_fieldnames, shape_reader, shape_handle = shape_reader_bundle
                try:
                    shape_fieldnames = _merge_fieldnames(shape_fieldnames, current_shape_fieldnames)
                    for row in shape_reader:
                        normalized_row = {key: (value or "").strip() for key, value in row.items()}
                        original_shape_id = (normalized_row.get("shape_id") or "").strip()
                        if original_shape_id not in shape_id_map:
                            continue
                        normalized_row["shape_id"] = shape_id_map[original_shape_id]
                        _append_jsonl_row(shape_spool, normalized_row)
                        shape_row_count += 1
                finally:
                    shape_handle.close()

                calendar_reader_bundle = _open_archive_reader(archive, "calendar.txt")
                if calendar_reader_bundle is not None:
                    current_calendar_fieldnames, calendar_reader, calendar_handle = calendar_reader_bundle
                    try:
                        calendar_fieldnames = _merge_fieldnames(calendar_fieldnames, current_calendar_fieldnames)
                        for row in calendar_reader:
                            normalized_row = {key: (value or "").strip() for key, value in row.items()}
                            original_service_id = (normalized_row.get("service_id") or "").strip()
                            if original_service_id not in service_id_map:
                                continue
                            normalized_row["service_id"] = service_id_map[original_service_id]
                            _append_jsonl_row(calendar_spool, normalized_row)
                            calendar_row_count += 1
                    finally:
                        calendar_handle.close()

                calendar_dates_reader_bundle = _open_archive_reader(archive, "calendar_dates.txt")
                if calendar_dates_reader_bundle is not None:
                    (
                        current_calendar_dates_fieldnames,
                        calendar_dates_reader,
                        calendar_dates_handle,
                    ) = calendar_dates_reader_bundle
                    try:
                        calendar_dates_fieldnames = _merge_fieldnames(
                            calendar_dates_fieldnames,
                            current_calendar_dates_fieldnames,
                        )
                        for row in calendar_dates_reader:
                            normalized_row = {key: (value or "").strip() for key, value in row.items()}
                            original_service_id = (normalized_row.get("service_id") or "").strip()
                            if original_service_id not in service_id_map:
                                continue
                            normalized_row["service_id"] = service_id_map[original_service_id]
                            _append_jsonl_row(calendar_dates_spool, normalized_row)
                            calendar_dates_row_count += 1
                    finally:
                        calendar_dates_handle.close()

                stop_observation_reader_bundle = _open_archive_reader(
                    archive,
                    STOP_OBSERVATIONS_FILENAME,
                )
                if stop_observation_reader_bundle is None:
                    raise ValueError(
                        f"{STOP_OBSERVATIONS_FILENAME} is required in the historic publication source archive."
                    )
                (
                    current_stop_observation_fieldnames,
                    stop_observation_reader,
                    stop_observation_handle,
                ) = stop_observation_reader_bundle
                try:
                    stop_observation_fieldnames = _merge_fieldnames(
                        stop_observation_fieldnames,
                        current_stop_observation_fieldnames,
                    )
                    for row in stop_observation_reader:
                        normalized_row = {key: (value or "").strip() for key, value in row.items()}
                        original_trip_id = (normalized_row.get("trip_id") or "").strip()
                        if original_trip_id not in trip_id_map:
                            continue
                        normalized_row["trip_id"] = trip_id_map[original_trip_id]
                        _append_jsonl_row(stop_observation_spool, normalized_row)
                        stop_observation_row_count += 1
                finally:
                    stop_observation_handle.close()

        if shape_row_count <= 0:
            raise RuntimeError("Combined rolling historic archive would contain no shapes.txt rows.")
        if stop_observation_row_count <= 0:
            raise RuntimeError(
                "Combined rolling historic archive would contain no stop_observations.txt rows."
            )

        oldest_month = publication_months[0].replace("-", "")
        latest_month = publication_months[-1].replace("-", "")
        artifact_stem = (
            f"511_{DERIVED_PUBLICATION_FEED_SCOPE}_{selected_agency_id}_{oldest_month}_{latest_month}_window{len(publication_months)}"
        )
        artifact_path = combined_acquisitions_root / f"{artifact_stem}.zip"
        metadata_path = combined_acquisitions_root / f"{artifact_stem}.json"

        retained_row_counts: dict[str, int] = {}
        with zipfile.ZipFile(
            artifact_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            retained_row_counts["routes.txt"] = _write_rows_to_zip(
                archive,
                "routes.txt",
                fieldnames=route_fieldnames,
                rows=list(routes_by_id.values()),
            )
            retained_row_counts["trips.txt"] = _write_jsonl_rows_to_zip(
                archive,
                "trips.txt",
                fieldnames=trip_fieldnames,
                spool_path=trip_spool,
            )
            retained_row_counts["stop_times.txt"] = _write_jsonl_rows_to_zip(
                archive,
                "stop_times.txt",
                fieldnames=stop_time_fieldnames,
                spool_path=stop_time_spool,
            )
            retained_row_counts["stops.txt"] = _write_rows_to_zip(
                archive,
                "stops.txt",
                fieldnames=stop_fieldnames,
                rows=list(stops_by_id.values()),
            )
            retained_row_counts["shapes.txt"] = _write_jsonl_rows_to_zip(
                archive,
                "shapes.txt",
                fieldnames=shape_fieldnames,
                spool_path=shape_spool,
            )
            if calendar_row_count > 0:
                retained_row_counts["calendar.txt"] = _write_jsonl_rows_to_zip(
                    archive,
                    "calendar.txt",
                    fieldnames=calendar_fieldnames,
                    spool_path=calendar_spool,
                )
            if calendar_dates_row_count > 0:
                retained_row_counts["calendar_dates.txt"] = _write_jsonl_rows_to_zip(
                    archive,
                    "calendar_dates.txt",
                    fieldnames=calendar_dates_fieldnames,
                    spool_path=calendar_dates_spool,
                )
            retained_row_counts[STOP_OBSERVATIONS_FILENAME] = _write_jsonl_rows_to_zip(
                archive,
                STOP_OBSERVATIONS_FILENAME,
                fieldnames=stop_observation_fieldnames,
                spool_path=stop_observation_spool,
            )

        with zipfile.ZipFile(artifact_path, mode="r") as archive:
            zip_member_names = tuple(sorted(archive.namelist()))

        metadata_payload = {
            "artifact_filename": artifact_path.name,
            "artifact_sha256": _hash_file(artifact_path),
            "artifact_size_bytes": artifact_path.stat().st_size,
            "combined_at": datetime.now(tz=UTC).isoformat(),
            "feed_scope": DERIVED_PUBLICATION_FEED_SCOPE,
            "operator_id": selected_agency_id,
            "publication_kind": PUBLICATION_KIND,
            "publication_window_months": publication_months,
            "publication_window_size_months": len(publication_months),
            "requested_historic_month": publication_months[-1],
            "requested_historic_value": f"{publication_months[-1]}-so",
            "requested_stop_observations": True,
            "required_core_files": ["routes.txt", "trips.txt", "stops.txt", "stop_times.txt", "shapes.txt"],
            "retained_row_counts": retained_row_counts,
            "service_files_present": tuple(
                file_name
                for file_name in ("calendar.txt", "calendar_dates.txt")
                if file_name in zip_member_names
            ),
            "selected_agency_id": selected_agency_id,
            "source_artifact_filenames": [
                str(json.loads(path.read_text(encoding="utf-8"))["artifact_filename"])
                for path in ordered_metadata_paths
            ],
            "source_feed_scope": "regional_historic_sf",
            "source_metadata_paths": [str(path) for path in ordered_metadata_paths],
            "source_system": "511",
            "stop_observations_present": True,
            "shapes_present": True,
            "zip_member_names": zip_member_names,
        }
        metadata_path.write_text(
            json.dumps(metadata_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return CombinedHistoricArchiveResult(
            artifact_path=artifact_path,
            metadata_path=metadata_path,
            retained_row_counts=retained_row_counts,
            publication_months=tuple(publication_months),
        )


def _publication_manifest_paths(publication_root: Path) -> tuple[Path, Path]:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return publication_root / f"{timestamp}.json", publication_root / "latest.json"


def _load_latest_publication_manifest(publication_root: Path) -> dict[str, Any] | None:
    latest_path = publication_root / "latest.json"
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text(encoding="utf-8"))


def _write_publication_manifest(
    publication_root: Path,
    payload: Mapping[str, Any],
) -> tuple[Path, Path]:
    publication_root.mkdir(parents=True, exist_ok=True)
    manifest_path, latest_manifest_path = _publication_manifest_paths(publication_root)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    latest_manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path, latest_manifest_path


def _artifact_path_from_metadata_payload(
    metadata_path: Path,
    metadata_payload: Mapping[str, Any],
) -> Path | None:
    artifact_filename = str(metadata_payload.get("artifact_filename") or "").strip()
    if not artifact_filename:
        return None
    return metadata_path.parent / artifact_filename


def _keep_paths_for_metadata(metadata_path: Path) -> set[Path]:
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    keep_paths = {metadata_path}
    artifact_path = _artifact_path_from_metadata_payload(metadata_path, payload)
    if artifact_path is not None:
        keep_paths.add(artifact_path)
    shape_backfill_manifest_path = str(payload.get("shape_backfill_manifest_path") or "").strip()
    if shape_backfill_manifest_path:
        keep_paths.add(Path(shape_backfill_manifest_path))
    return keep_paths


def _prune_directory_to_keep_paths(root: Path, keep_paths: set[Path]) -> None:
    if not root.exists():
        return
    normalized_keep_paths = {path.resolve() for path in keep_paths}
    for path in root.iterdir():
        if path.resolve() in normalized_keep_paths:
            continue
        if path.is_file():
            path.unlink()


def _prune_publication_storage(
    *,
    active_metadata_path: Path,
    monthly_metadata_paths: Iterable[Path],
    combined_metadata_path: Path,
    publication_manifest_path: Path,
    latest_publication_manifest_path: Path,
    cutover_manifest_path: Path,
    cutover_latest_manifest_path: Path,
    cutover_log_path: Path,
    cutover_latest_log_path: Path,
    active_root: Path,
    historic_root: Path,
    derived_root: Path,
    combined_root: Path,
    publication_root: Path,
    cutover_root: Path,
) -> None:
    _prune_directory_to_keep_paths(
        active_root,
        _keep_paths_for_metadata(active_metadata_path),
    )
    _prune_directory_to_keep_paths(
        historic_root,
        {
            path
            for metadata_path in monthly_metadata_paths
            for path in _keep_paths_for_metadata(metadata_path)
        },
    )
    _prune_directory_to_keep_paths(
        derived_root,
        {
            path
            for metadata_path in monthly_metadata_paths
            for path in _keep_paths_for_metadata(metadata_path)
        },
    )
    _prune_directory_to_keep_paths(
        combined_root,
        _keep_paths_for_metadata(combined_metadata_path),
    )
    _prune_directory_to_keep_paths(
        publication_root,
        {
            publication_manifest_path,
            latest_publication_manifest_path,
        },
    )
    _prune_directory_to_keep_paths(
        cutover_root,
        {
            cutover_manifest_path,
            cutover_latest_manifest_path,
            cutover_log_path,
            cutover_latest_log_path,
        },
    )


def _publish_month_window(
    *,
    action: str,
    publication_months: tuple[str, ...],
    latest_available_month: str,
    historic_agency_id: str,
    publication_root: Path,
    publication_cutover_root: Path,
    active_acquisitions_root: Path,
    historic_acquisitions_root: Path,
    derived_acquisitions_root: Path,
    combined_acquisitions_root: Path,
    active_metadata_path: Path | None = None,
    reuse_existing_raw: bool = True,
    skip_dbt: bool = False,
) -> RollingPublicationResult:
    api_key = get_511_api_key()
    if active_metadata_path is None:
        active_metadata_path = fetch_active_gtfs_archive(
            api_key=api_key,
            acquisitions_root=active_acquisitions_root,
        ).metadata_path

    monthly_metadata_paths: list[Path] = []
    for historic_month in publication_months:
        historic_fetch = fetch_historic_rg_gtfs_archive(
            api_key=api_key,
            historic_month=historic_month,
            include_stop_observations=True,
            acquisitions_root=historic_acquisitions_root,
        )
        historic_extract = extract_sf_historic_archive(
            metadata_path=historic_fetch.metadata_path,
            selected_agency_id=historic_agency_id,
            api_key=api_key,
            active_metadata_path=active_metadata_path,
            acquisitions_root=derived_acquisitions_root,
        )
        monthly_metadata_paths.append(historic_extract.metadata_path)

    combined_archive = combine_historic_month_archives(
        metadata_paths=monthly_metadata_paths,
        selected_agency_id=historic_agency_id,
        combined_acquisitions_root=combined_acquisitions_root,
    )

    publication_cutover_root.mkdir(parents=True, exist_ok=True)
    run_timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = publication_cutover_root / f"{run_timestamp}.log"
    latest_log_path = publication_cutover_root / "latest.log"
    latest_log_path.write_text("", encoding="utf-8")

    cutover_result = materialize_prepared_historic_publication(
        active_metadata_path=active_metadata_path,
        historic_source_metadata_path=combined_archive.metadata_path,
        historic_gtfs_metadata_path=combined_archive.metadata_path,
        historic_feed_scope=DERIVED_PUBLICATION_FEED_SCOPE,
        historic_month=latest_available_month,
        historic_agency_id=historic_agency_id,
        cutover_root=publication_cutover_root,
        log_path=log_path,
        latest_log_path=latest_log_path,
        reuse_existing_raw=reuse_existing_raw,
        skip_dbt=skip_dbt,
        manifest_extra={
            "rolling_publication_months": list(publication_months),
            "rolling_publication_kind": PUBLICATION_KIND,
        },
    )

    publication_payload = {
        "action": action,
        "active_metadata_path": str(active_metadata_path),
        "combined_metadata_path": str(combined_archive.metadata_path),
        "cutover_manifest_path": str(cutover_result.manifest_path),
        "historic_agency_id": historic_agency_id,
        "latest_available_month": latest_available_month,
        "publication_built_at": datetime.now(tz=UTC).isoformat(),
        "publication_kind": PUBLICATION_KIND,
        "publication_months": list(publication_months),
        "route_count_with_metrics": cutover_result.route_count_with_metrics,
        "map_route_count": cutover_result.map_route_count,
        "top_route_ids": list(cutover_result.top_route_ids),
    }
    publication_manifest_path, latest_publication_manifest_path = _write_publication_manifest(
        publication_root,
        publication_payload,
    )
    _prune_publication_storage(
        active_metadata_path=active_metadata_path,
        monthly_metadata_paths=monthly_metadata_paths,
        combined_metadata_path=combined_archive.metadata_path,
        publication_manifest_path=publication_manifest_path,
        latest_publication_manifest_path=latest_publication_manifest_path,
        cutover_manifest_path=cutover_result.manifest_path,
        cutover_latest_manifest_path=cutover_result.latest_manifest_path,
        cutover_log_path=cutover_result.log_path,
        cutover_latest_log_path=cutover_result.latest_log_path,
        active_root=active_acquisitions_root,
        historic_root=historic_acquisitions_root,
        derived_root=derived_acquisitions_root,
        combined_root=combined_acquisitions_root,
        publication_root=publication_root,
        cutover_root=publication_cutover_root,
    )

    return RollingPublicationResult(
        action=action,
        historic_agency_id=historic_agency_id,
        latest_available_month=latest_available_month,
        publication_months=publication_months,
        publication_manifest_path=publication_manifest_path,
        latest_publication_manifest_path=latest_publication_manifest_path,
        active_metadata_path=active_metadata_path,
        combined_metadata_path=combined_archive.metadata_path,
        cutover_manifest_path=cutover_result.manifest_path,
        availability_status_code=200,
        availability_request_method="bootstrap",
        published=True,
        route_count_with_metrics=cutover_result.route_count_with_metrics,
        map_route_count=cutover_result.map_route_count,
        top_route_ids=tuple(cutover_result.top_route_ids),
    )


def bootstrap_rolling_historical_publication(
    *,
    historic_agency_id: str = DEFAULT_HISTORIC_AGENCY_ID,
    latest_available_month: str | None = None,
    current_date: date | None = None,
    publication_root: Path = DEFAULT_PUBLICATION_ROOT,
    publication_cutover_root: Path = DEFAULT_PUBLICATION_CUTOVER_ROOT,
    active_acquisitions_root: Path = DEFAULT_ACTIVE_PUBLICATION_ACQUISITIONS_ROOT,
    historic_acquisitions_root: Path = DEFAULT_HISTORIC_PUBLICATION_ACQUISITIONS_ROOT,
    derived_acquisitions_root: Path = DEFAULT_DERIVED_PUBLICATION_ACQUISITIONS_ROOT,
    combined_acquisitions_root: Path = DEFAULT_COMBINED_ACQUISITIONS_ROOT,
    window_months: int = DEFAULT_ROLLING_WINDOW_MONTHS,
    skip_dbt: bool = False,
) -> RollingPublicationResult:
    api_key = get_511_api_key()
    availability = (
        check_newest_available_completed_month(api_key=api_key, current_date=current_date)
        if latest_available_month is None
        else check_historic_rg_gtfs_archive_availability(
            api_key=api_key,
            historic_month=latest_available_month,
            include_stop_observations=True,
        )
    )
    if not availability.available:
        raise RuntimeError(
            f"Historic archive for newest completed month {availability.historic_month} is not available yet."
        )
    publication_months = build_trailing_publication_months(
        availability.historic_month,
        window_months=window_months,
    )
    return _publish_month_window(
        action="bootstrap",
        publication_months=publication_months,
        latest_available_month=availability.historic_month,
        historic_agency_id=historic_agency_id,
        publication_root=publication_root,
        publication_cutover_root=publication_cutover_root,
        active_acquisitions_root=active_acquisitions_root,
        historic_acquisitions_root=historic_acquisitions_root,
        derived_acquisitions_root=derived_acquisitions_root,
        combined_acquisitions_root=combined_acquisitions_root,
        skip_dbt=skip_dbt,
    )


def advance_rolling_historical_publication(
    *,
    historic_agency_id: str = DEFAULT_HISTORIC_AGENCY_ID,
    target_month: str | None = None,
    current_date: date | None = None,
    publication_root: Path = DEFAULT_PUBLICATION_ROOT,
    publication_cutover_root: Path = DEFAULT_PUBLICATION_CUTOVER_ROOT,
    active_acquisitions_root: Path = DEFAULT_ACTIVE_PUBLICATION_ACQUISITIONS_ROOT,
    historic_acquisitions_root: Path = DEFAULT_HISTORIC_PUBLICATION_ACQUISITIONS_ROOT,
    derived_acquisitions_root: Path = DEFAULT_DERIVED_PUBLICATION_ACQUISITIONS_ROOT,
    combined_acquisitions_root: Path = DEFAULT_COMBINED_ACQUISITIONS_ROOT,
    window_months: int = DEFAULT_ROLLING_WINDOW_MONTHS,
    skip_dbt: bool = False,
) -> RollingPublicationResult:
    existing_manifest = _load_latest_publication_manifest(publication_root)
    if existing_manifest is None:
        raise RuntimeError("No rolling publication manifest exists yet. Run bootstrap first.")

    api_key = get_511_api_key()
    availability = (
        check_newest_available_completed_month(api_key=api_key, current_date=current_date)
        if target_month is None
        else check_historic_rg_gtfs_archive_availability(
            api_key=api_key,
            historic_month=target_month,
            include_stop_observations=True,
        )
    )
    latest_published_month = str(existing_manifest["latest_available_month"])
    publication_manifest_path = publication_root / "latest.json"

    if not availability.available:
        return RollingPublicationResult(
            action="unavailable",
            historic_agency_id=historic_agency_id,
            latest_available_month=availability.historic_month,
            publication_months=tuple(existing_manifest.get("publication_months", [])),
            publication_manifest_path=publication_manifest_path,
            latest_publication_manifest_path=publication_manifest_path,
            active_metadata_path=None,
            combined_metadata_path=None,
            cutover_manifest_path=None,
            availability_status_code=availability.status_code,
            availability_request_method=availability.request_method,
            published=False,
            route_count_with_metrics=None,
            map_route_count=None,
            top_route_ids=(),
        )

    if validate_historic_month(availability.historic_month) == validate_historic_month(
        latest_published_month
    ):
        return RollingPublicationResult(
            action="already_published",
            historic_agency_id=historic_agency_id,
            latest_available_month=availability.historic_month,
            publication_months=tuple(existing_manifest.get("publication_months", [])),
            publication_manifest_path=publication_manifest_path,
            latest_publication_manifest_path=publication_manifest_path,
            active_metadata_path=None,
            combined_metadata_path=None,
            cutover_manifest_path=None,
            availability_status_code=availability.status_code,
            availability_request_method=availability.request_method,
            published=False,
            route_count_with_metrics=None,
            map_route_count=None,
            top_route_ids=(),
        )

    publication_months = build_trailing_publication_months(
        availability.historic_month,
        window_months=window_months,
    )
    return _publish_month_window(
        action="advance",
        publication_months=publication_months,
        latest_available_month=availability.historic_month,
        historic_agency_id=historic_agency_id,
        publication_root=publication_root,
        publication_cutover_root=publication_cutover_root,
        active_acquisitions_root=active_acquisitions_root,
        historic_acquisitions_root=historic_acquisitions_root,
        derived_acquisitions_root=derived_acquisitions_root,
        combined_acquisitions_root=combined_acquisitions_root,
        skip_dbt=skip_dbt,
    )


def _parse_current_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check-newest-available",
        help="Check whether the newest completed historic month is available from 511.",
    )
    check_parser.add_argument("--current-date", default=None, help="Override current date (YYYY-MM-DD).")

    bootstrap_parser = subparsers.add_parser(
        "bootstrap-window",
        help="Bootstrap the first rolling historical publication window.",
    )
    bootstrap_parser.add_argument("--current-date", default=None, help="Override current date (YYYY-MM-DD).")
    bootstrap_parser.add_argument("--latest-available-month", default=None, help="Explicit newest available month (YYYY-MM).")
    bootstrap_parser.add_argument(
        "--window-months",
        type=int,
        default=DEFAULT_ROLLING_WINDOW_MONTHS,
        help="Number of trailing months to retain in the live publication window.",
    )
    bootstrap_parser.add_argument("--skip-dbt", action="store_true")

    advance_parser = subparsers.add_parser(
        "advance-window",
        help="Advance the rolling historical publication window if a newer month is available.",
    )
    advance_parser.add_argument("--current-date", default=None, help="Override current date (YYYY-MM-DD).")
    advance_parser.add_argument("--target-month", default=None, help="Explicit target month to publish (YYYY-MM).")
    advance_parser.add_argument(
        "--window-months",
        type=int,
        default=DEFAULT_ROLLING_WINDOW_MONTHS,
        help="Number of trailing months to retain in the live publication window.",
    )
    advance_parser.add_argument("--skip-dbt", action="store_true")

    args = parser.parse_args()
    if args.command == "check-newest-available":
        result = check_newest_available_completed_month(
            api_key=get_511_api_key(),
            current_date=_parse_current_date(args.current_date),
        )
        print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
        return 0

    if args.command == "bootstrap-window":
        result = bootstrap_rolling_historical_publication(
            current_date=_parse_current_date(args.current_date),
            latest_available_month=args.latest_available_month,
            window_months=args.window_months,
            skip_dbt=args.skip_dbt,
        )
        print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
        return 0

    result = advance_rolling_historical_publication(
        current_date=_parse_current_date(args.current_date),
        target_month=args.target_month,
        window_months=args.window_months,
        skip_dbt=args.skip_dbt,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
