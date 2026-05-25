"""Fetch and archive monthly historic 511 regional GTFS feeds."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from muni_lta_pipeline.active_gtfs_fetch import (
    CORE_GTFS_FILES,
    DEFAULT_511_GTFS_FEED_URL,
    DEFAULT_SOURCE_SYSTEM,
    get_511_api_key,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ACQUISITIONS_ROOT = REPO_ROOT / "artifacts" / "acquisitions" / "511" / "regional_historic"
DEFAULT_OPERATOR_ID = "RG"
DEFAULT_FEED_SCOPE = "regional_historic"
STOP_OBSERVATIONS_FILENAME = "stop_observations.txt"
HISTORIC_MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
HISTORIC_REQUIRED_CORE_FILES = tuple(
    file_name for file_name in CORE_GTFS_FILES if file_name != "shapes.txt"
)


@dataclass(frozen=True)
class HistoricAcquisitionMetadata:
    """Provenance and validation details for a fetched historic GTFS archive."""

    source_system: str
    feed_scope: str
    operator_id: str
    requested_historic_month: str
    requested_historic_value: str
    requested_stop_observations: bool
    requested_url: str
    fetched_at: str
    artifact_filename: str
    artifact_sha256: str
    artifact_size_bytes: int
    zip_member_names: tuple[str, ...]
    required_core_files: tuple[str, ...]
    service_files_present: tuple[str, ...]
    stop_observations_present: bool
    shapes_present: bool = True


@dataclass(frozen=True)
class HistoricAcquisitionResult:
    """Paths and metadata for a completed historic GTFS acquisition."""

    artifact_path: Path
    metadata_path: Path
    metadata: HistoricAcquisitionMetadata


@dataclass(frozen=True)
class HistoricAvailabilityResult:
    """Availability probe result for a historic 511 regional GTFS archive."""

    historic_month: str
    include_stop_observations: bool
    requested_url: str
    available: bool
    checked_at: str
    request_method: str
    status_code: int


def validate_historic_month(historic_month: str) -> str:
    """Validate the 511 historic month selector (YYYY-MM)."""

    if not HISTORIC_MONTH_PATTERN.fullmatch(historic_month):
        raise ValueError(
            "historic_month must be in YYYY-MM format, e.g. 2023-02."
        )

    year_text, month_text = historic_month.split("-", 1)
    month = int(month_text)
    if month < 1 or month > 12:
        raise ValueError(
            "historic_month must contain a valid month between 01 and 12."
        )

    return f"{int(year_text):04d}-{month:02d}"


def build_historic_rg_gtfs_url(
    api_key: str,
    *,
    historic_month: str,
    include_stop_observations: bool = False,
    operator_id: str = DEFAULT_OPERATOR_ID,
    base_url: str = DEFAULT_511_GTFS_FEED_URL,
) -> str:
    """Build the 511 historic regional GTFS download URL."""

    normalized_month = validate_historic_month(historic_month)
    historic_value = normalized_month + ("-so" if include_stop_observations else "")
    return (
        f"{base_url}?api_key={api_key}&operator_id={operator_id}"
        f"&historic={historic_value}"
    )


def validate_historic_gtfs_zip_bytes(
    payload: bytes,
    *,
    require_stop_observations: bool = False,
) -> tuple[tuple[str, ...], tuple[str, ...], bool, bool]:
    """Validate a historic GTFS archive and its stop-observations variant behavior."""
    from io import BytesIO
    import zipfile

    with zipfile.ZipFile(BytesIO(payload), mode="r") as archive:
        member_names = tuple(sorted(archive.namelist()))

    missing_core = [
        name for name in HISTORIC_REQUIRED_CORE_FILES if name not in member_names
    ]
    if missing_core:
        raise ValueError(
            "Historic GTFS archive is missing required core files: "
            + ", ".join(sorted(missing_core))
        )

    service_files_present = tuple(
        name for name in ("calendar.txt", "calendar_dates.txt") if name in member_names
    )
    if not service_files_present:
        raise ValueError(
            "Historic GTFS archive is missing both service-calendar files: "
            "calendar.txt and calendar_dates.txt."
        )

    shapes_present = "shapes.txt" in member_names
    stop_observations_present = STOP_OBSERVATIONS_FILENAME in member_names

    if require_stop_observations and not stop_observations_present:
        raise ValueError(
            "Historic GTFS archive is missing stop_observations.txt for a '-so' request."
        )

    if not require_stop_observations and stop_observations_present:
        raise ValueError(
            "Historic GTFS archive unexpectedly contains stop_observations.txt for a plain historic request."
        )

    return member_names, service_files_present, shapes_present, stop_observations_present


def fetch_historic_rg_gtfs_archive(
    *,
    api_key: str,
    historic_month: str,
    include_stop_observations: bool = False,
    source_system: str = DEFAULT_SOURCE_SYSTEM,
    feed_scope: str = DEFAULT_FEED_SCOPE,
    operator_id: str = DEFAULT_OPERATOR_ID,
    base_url: str = DEFAULT_511_GTFS_FEED_URL,
    acquisitions_root: Path = DEFAULT_ACQUISITIONS_ROOT,
    timeout_seconds: int = 60,
) -> HistoricAcquisitionResult:
    """Download, validate, and archive a monthly historic regional GTFS zip."""

    normalized_month = validate_historic_month(historic_month)
    requested_historic_value = normalized_month + (
        "-so" if include_stop_observations else ""
    )
    requested_url = build_historic_rg_gtfs_url(
        api_key,
        historic_month=normalized_month,
        include_stop_observations=include_stop_observations,
        operator_id=operator_id,
        base_url=base_url,
    )
    request = Request(
        requested_url,
        headers={"User-Agent": "muni-lost-time-atlas/0.1"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read()

    fetched_at = datetime.now(tz=UTC)
    member_names, service_files_present, shapes_present, stop_observations_present = (
        validate_historic_gtfs_zip_bytes(
            payload,
            require_stop_observations=include_stop_observations,
        )
    )
    sha256 = hashlib.sha256(payload).hexdigest()
    timestamp_label = fetched_at.strftime("%Y%m%dT%H%M%SZ")

    acquisitions_root.mkdir(parents=True, exist_ok=True)
    stop_obs_label = "with_so" if include_stop_observations else "plain"
    month_label = normalized_month.replace("-", "")
    file_stem = (
        f"{source_system}_{feed_scope}_{operator_id}_{month_label}_{stop_obs_label}_{timestamp_label}"
    )
    artifact_path = acquisitions_root / f"{file_stem}.zip"
    metadata_path = acquisitions_root / f"{file_stem}.json"

    artifact_path.write_bytes(payload)
    metadata = HistoricAcquisitionMetadata(
        source_system=source_system,
        feed_scope=feed_scope,
        operator_id=operator_id,
        requested_historic_month=normalized_month,
        requested_historic_value=requested_historic_value,
        requested_stop_observations=include_stop_observations,
        requested_url=requested_url,
        fetched_at=fetched_at.isoformat(),
        artifact_filename=artifact_path.name,
        artifact_sha256=sha256,
        artifact_size_bytes=len(payload),
        zip_member_names=member_names,
        required_core_files=HISTORIC_REQUIRED_CORE_FILES,
        service_files_present=service_files_present,
        shapes_present=shapes_present,
        stop_observations_present=stop_observations_present,
    )
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return HistoricAcquisitionResult(
        artifact_path=artifact_path,
        metadata_path=metadata_path,
        metadata=metadata,
    )


def check_historic_rg_gtfs_archive_availability(
    *,
    api_key: str,
    historic_month: str,
    include_stop_observations: bool = False,
    operator_id: str = DEFAULT_OPERATOR_ID,
    base_url: str = DEFAULT_511_GTFS_FEED_URL,
    timeout_seconds: int = 30,
) -> HistoricAvailabilityResult:
    """Check whether a historic 511 regional GTFS archive is available without downloading it fully."""

    normalized_month = validate_historic_month(historic_month)
    requested_url = build_historic_rg_gtfs_url(
        api_key,
        historic_month=normalized_month,
        include_stop_observations=include_stop_observations,
        operator_id=operator_id,
        base_url=base_url,
    )
    checked_at = datetime.now(tz=UTC).isoformat()
    request_attempts = (
        ("HEAD", {"User-Agent": "muni-lost-time-atlas/0.1"}),
        ("GET", {"User-Agent": "muni-lost-time-atlas/0.1", "Range": "bytes=0-0"}),
    )
    fallback_status_codes = {400, 405, 501}
    last_http_error: HTTPError | None = None

    for method, headers in request_attempts:
        request = Request(requested_url, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                status_code = int(getattr(response, "status", response.getcode()))
                return HistoricAvailabilityResult(
                    historic_month=normalized_month,
                    include_stop_observations=include_stop_observations,
                    requested_url=requested_url,
                    available=200 <= status_code < 300,
                    checked_at=checked_at,
                    request_method=method,
                    status_code=status_code,
                )
        except HTTPError as exc:
            if exc.code == 404:
                return HistoricAvailabilityResult(
                    historic_month=normalized_month,
                    include_stop_observations=include_stop_observations,
                    requested_url=requested_url,
                    available=False,
                    checked_at=checked_at,
                    request_method=method,
                    status_code=exc.code,
                )
            if method == "HEAD" and exc.code in fallback_status_codes:
                last_http_error = exc
                continue
            raise

    assert last_http_error is not None
    raise last_http_error


def _serialize_result(result: HistoricAcquisitionResult) -> dict[str, Any]:
    return {
        "artifact_path": str(result.artifact_path),
        "metadata_path": str(result.metadata_path),
        "metadata": asdict(result.metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--historic-month",
        required=True,
        help="Requested historic regional feed month in YYYY-MM format.",
    )
    parser.add_argument(
        "--with-stop-observations",
        action="store_true",
        help="Request the historic '-so' variant that includes stop_observations.txt.",
    )
    parser.add_argument(
        "--acquisitions-root",
        type=Path,
        default=DEFAULT_ACQUISITIONS_ROOT,
        help="Directory where acquisition artifacts should be written.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        help="HTTP timeout for the GTFS feed request.",
    )
    args = parser.parse_args()

    result = fetch_historic_rg_gtfs_archive(
        api_key=get_511_api_key(),
        historic_month=args.historic_month,
        include_stop_observations=args.with_stop_observations,
        acquisitions_root=args.acquisitions_root,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(_serialize_result(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
