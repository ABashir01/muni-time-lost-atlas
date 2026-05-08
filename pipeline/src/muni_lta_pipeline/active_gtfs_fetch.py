"""Fetch and archive the active operator-specific Muni GTFS feed from 511."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"
DEFAULT_ACQUISITIONS_ROOT = REPO_ROOT / "artifacts" / "acquisitions" / "511" / "operator_active"
DEFAULT_511_GTFS_FEED_URL = "https://api.511.org/transit/datafeeds"
DEFAULT_OPERATOR_ID = "SF"
DEFAULT_SOURCE_SYSTEM = "511"
DEFAULT_FEED_SCOPE = "operator_active"
CORE_GTFS_FILES = (
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
    "shapes.txt",
)
SERVICE_GTFS_FILES = ("calendar.txt", "calendar_dates.txt")


@dataclass(frozen=True)
class AcquisitionMetadata:
    """Provenance and validation details for a fetched GTFS archive."""

    source_system: str
    feed_scope: str
    operator_id: str
    requested_url: str
    fetched_at: str
    artifact_filename: str
    artifact_sha256: str
    artifact_size_bytes: int
    zip_member_names: tuple[str, ...]
    required_core_files: tuple[str, ...]
    service_files_present: tuple[str, ...]


@dataclass(frozen=True)
class AcquisitionResult:
    """Paths and metadata for a completed active GTFS acquisition."""

    artifact_path: Path
    metadata_path: Path
    metadata: AcquisitionMetadata


def load_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    """Read simple KEY=VALUE settings from the repo-root .env file."""

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


def get_effective_environ(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Merge repo-root .env values with the current process environment."""

    merged = load_env_file()
    if environ:
        merged.update(environ)
    else:
        merged.update(os.environ)
    return merged


def build_active_gtfs_url(
    api_key: str,
    *,
    operator_id: str = DEFAULT_OPERATOR_ID,
    base_url: str = DEFAULT_511_GTFS_FEED_URL,
) -> str:
    """Build the operator-specific 511 GTFS download URL."""

    query = urlencode({"api_key": api_key, "operator_id": operator_id})
    return f"{base_url}?{query}"


def validate_gtfs_zip_bytes(payload: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Validate that the archive looks like a usable active GTFS download."""

    from io import BytesIO

    with zipfile.ZipFile(BytesIO(payload), mode="r") as archive:
        member_names = tuple(sorted(archive.namelist()))

    missing_core = [name for name in CORE_GTFS_FILES if name not in member_names]
    if missing_core:
        raise ValueError(
            "GTFS archive is missing required core files: "
            + ", ".join(sorted(missing_core))
        )

    service_files_present = tuple(
        name for name in SERVICE_GTFS_FILES if name in member_names
    )
    if not service_files_present:
        raise ValueError(
            "GTFS archive is missing both service-calendar files: "
            "calendar.txt and calendar_dates.txt."
        )

    return member_names, service_files_present


def validate_gtfs_zip_file(path: Path) -> AcquisitionMetadata:
    """Validate an existing GTFS zip and return derived metadata."""

    payload = path.read_bytes()
    member_names, service_files_present = validate_gtfs_zip_bytes(payload)
    sha256 = hashlib.sha256(payload).hexdigest()
    return AcquisitionMetadata(
        source_system=DEFAULT_SOURCE_SYSTEM,
        feed_scope=DEFAULT_FEED_SCOPE,
        operator_id=DEFAULT_OPERATOR_ID,
        requested_url="local_validation_only",
        fetched_at=datetime.now(tz=UTC).isoformat(),
        artifact_filename=path.name,
        artifact_sha256=sha256,
        artifact_size_bytes=len(payload),
        zip_member_names=member_names,
        required_core_files=CORE_GTFS_FILES,
        service_files_present=service_files_present,
    )


def fetch_active_gtfs_archive(
    *,
    api_key: str,
    operator_id: str = DEFAULT_OPERATOR_ID,
    source_system: str = DEFAULT_SOURCE_SYSTEM,
    feed_scope: str = DEFAULT_FEED_SCOPE,
    base_url: str = DEFAULT_511_GTFS_FEED_URL,
    acquisitions_root: Path = DEFAULT_ACQUISITIONS_ROOT,
    timeout_seconds: int = 60,
) -> AcquisitionResult:
    """Download, validate, and archive the active operator-specific GTFS zip."""

    requested_url = build_active_gtfs_url(
        api_key,
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
    member_names, service_files_present = validate_gtfs_zip_bytes(payload)
    sha256 = hashlib.sha256(payload).hexdigest()
    timestamp_label = fetched_at.strftime("%Y%m%dT%H%M%SZ")

    acquisitions_root.mkdir(parents=True, exist_ok=True)
    file_stem = f"{source_system}_{feed_scope}_{operator_id}_{timestamp_label}"
    artifact_path = acquisitions_root / f"{file_stem}.zip"
    metadata_path = acquisitions_root / f"{file_stem}.json"

    artifact_path.write_bytes(payload)
    metadata = AcquisitionMetadata(
        source_system=source_system,
        feed_scope=feed_scope,
        operator_id=operator_id,
        requested_url=requested_url,
        fetched_at=fetched_at.isoformat(),
        artifact_filename=artifact_path.name,
        artifact_sha256=sha256,
        artifact_size_bytes=len(payload),
        zip_member_names=member_names,
        required_core_files=CORE_GTFS_FILES,
        service_files_present=service_files_present,
    )
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return AcquisitionResult(
        artifact_path=artifact_path,
        metadata_path=metadata_path,
        metadata=metadata,
    )


def get_511_api_key(environ: Mapping[str, str] | None = None) -> str:
    """Resolve the 511 API key from .env or environment variables."""

    env = get_effective_environ(environ)
    api_key = env.get("TRANSIT_511_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing TRANSIT_511_API_KEY. Set it in .env or the current environment."
        )
    return api_key


def _serialize_result(result: AcquisitionResult) -> dict[str, Any]:
    return {
        "artifact_path": str(result.artifact_path),
        "metadata_path": str(result.metadata_path),
        "metadata": asdict(result.metadata),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operator-id",
        default=DEFAULT_OPERATOR_ID,
        help="511 operator_id to fetch. Defaults to SF for SFMTA/Muni.",
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

    result = fetch_active_gtfs_archive(
        api_key=get_511_api_key(),
        operator_id=args.operator_id,
        acquisitions_root=args.acquisitions_root,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(_serialize_result(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
