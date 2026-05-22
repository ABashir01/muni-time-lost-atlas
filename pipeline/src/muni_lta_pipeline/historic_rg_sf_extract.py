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

from muni_lta_pipeline.active_gtfs_fetch import CORE_GTFS_FILES
from muni_lta_pipeline.gtfs_static_fixture_ingest import REPO_ROOT
from muni_lta_pipeline.historic_rg_feed_fetch import STOP_OBSERVATIONS_FILENAME


DEFAULT_DERIVED_ACQUISITIONS_ROOT = (
    REPO_ROOT / "artifacts" / "acquisitions" / "511" / "regional_historic_sf"
)
DEFAULT_SELECTED_AGENCY_ID = "SF"
DERIVED_FEED_SCOPE = "regional_historic_sf"
OPTIONAL_GTFS_FILES = ("calendar.txt", "calendar_dates.txt")


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


@dataclass(frozen=True)
class HistoricSfExtractionResult:
    artifact_path: Path
    metadata_path: Path
    metadata: HistoricSfExtractionMetadata
    reused_existing: bool


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


def _resolve_artifact_path(metadata_path: Path, metadata: Mapping[str, Any]) -> Path:
    artifact_filename = str(metadata["artifact_filename"]).strip()
    if not artifact_filename:
        raise ValueError("Historic acquisition metadata must include artifact_filename.")

    artifact_path = metadata_path.parent / artifact_filename
    if not artifact_path.exists():
        raise FileNotFoundError(f"Historic archive zip not found: {artifact_path}")
    return artifact_path


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
    route_ids: set[str],
) -> tuple[set[str], set[str], set[str], int]:
    trip_ids: set[str] = set()
    service_ids: set[str] = set()
    shape_ids: set[str] = set()
    retained_row_count = 0
    with archive.open("trips.txt", mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError("trips.txt has no header row.")

        for row in reader:
            route_id = (row.get("route_id") or "").strip()
            if route_id not in route_ids:
                continue

            trip_id = (row.get("trip_id") or "").strip()
            service_id = (row.get("service_id") or "").strip()
            shape_id = (row.get("shape_id") or "").strip()
            if trip_id:
                trip_ids.add(trip_id)
            if service_id:
                service_ids.add(service_id)
            if shape_id:
                shape_ids.add(shape_id)
            retained_row_count += 1

    if not trip_ids:
        raise ValueError("No trips remained after filtering the historic archive to selected routes.")
    return trip_ids, service_ids, shape_ids, retained_row_count


def _read_selected_stop_ids(
    archive: zipfile.ZipFile,
    *,
    trip_ids: set[str],
) -> tuple[set[str], int]:
    stop_ids: set[str] = set()
    retained_row_count = 0
    with archive.open("stop_times.txt", mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        if reader.fieldnames is None:
            raise ValueError("stop_times.txt has no header row.")

        for row in reader:
            trip_id = (row.get("trip_id") or "").strip()
            if trip_id not in trip_ids:
                continue
            stop_id = (row.get("stop_id") or "").strip()
            if stop_id:
                stop_ids.add(stop_id)
            retained_row_count += 1

    return stop_ids, retained_row_count


def _build_metadata(
    *,
    metadata_path: Path,
    source_metadata: Mapping[str, Any],
    artifact_path: Path,
    retained_row_counts: Mapping[str, int],
    selected_agency_id: str,
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
        stop_observations_present=STOP_OBSERVATIONS_FILENAME in zip_member_names,
        zip_member_names=zip_member_names,
    )


def extract_sf_historic_archive(
    *,
    metadata_path: Path,
    selected_agency_id: str = DEFAULT_SELECTED_AGENCY_ID,
    acquisitions_root: Path = DEFAULT_DERIVED_ACQUISITIONS_ROOT,
) -> HistoricSfExtractionResult:
    source_metadata = _load_metadata(metadata_path)
    if (
        str(source_metadata.get("feed_scope")) == DERIVED_FEED_SCOPE
        and str(source_metadata.get("selected_agency_id")) == selected_agency_id
    ):
        artifact_path = _resolve_artifact_path(metadata_path, source_metadata)
        return HistoricSfExtractionResult(
            artifact_path=artifact_path,
            metadata_path=metadata_path,
            metadata=HistoricSfExtractionMetadata(**source_metadata),
            reused_existing=True,
        )

    source_artifact_path = _resolve_artifact_path(metadata_path, source_metadata)
    derived_stem = _derived_stem(source_metadata, selected_agency_id=selected_agency_id)
    acquisitions_root.mkdir(parents=True, exist_ok=True)
    artifact_path = acquisitions_root / f"{derived_stem}.zip"
    metadata_output_path = acquisitions_root / f"{derived_stem}.json"

    if artifact_path.exists() and metadata_output_path.exists():
        existing_metadata = HistoricSfExtractionMetadata(
            **json.loads(metadata_output_path.read_text(encoding="utf-8"))
        )
        return HistoricSfExtractionResult(
            artifact_path=artifact_path,
            metadata_path=metadata_output_path,
            metadata=existing_metadata,
            reused_existing=True,
        )

    retained_row_counts: dict[str, int] = {}
    with zipfile.ZipFile(source_artifact_path, mode="r") as source_archive:
        route_ids, retained_row_counts["routes.txt"] = _read_selected_routes(
            source_archive,
            selected_agency_id=selected_agency_id,
        )
        trip_ids, service_ids, shape_ids, retained_row_counts["trips.txt"] = _read_selected_trips(
            source_archive,
            route_ids=route_ids,
        )
        stop_ids, retained_row_counts["stop_times.txt"] = _read_selected_stop_ids(
            source_archive,
            trip_ids=trip_ids,
        )

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
            retained_row_counts["trips.txt"] = _stream_filter_member(
                source_archive,
                destination_archive,
                "trips.txt",
                keep_row=lambda row: (row.get("trip_id") or "").strip() in trip_ids,
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
            retained_row_counts["shapes.txt"] = _stream_filter_member(
                source_archive,
                destination_archive,
                "shapes.txt",
                keep_row=lambda row: (row.get("shape_id") or "").strip() in shape_ids,
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
