"""Fetch and cache 511 Shapes API geometry for missing historic shape_ids."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEFAULT_511_SHAPES_URL = "https://api.511.org/transit/shapes"
DEFAULT_SOURCE_SYSTEM = "511"


@dataclass(frozen=True)
class ShapeBackfillArtifact:
    shape_id: str
    representative_trip_id: str
    shapes_api_trip_id: str
    cache_path: Path
    point_count: int
    reused_cached: bool
    fetched_at: str
    requested_url: str


@dataclass(frozen=True)
class ShapeBackfillResult:
    shape_rows: tuple[dict[str, str], ...]
    request_count: int
    cache_hit_count: int
    successful_shape_count: int
    failure_shape_ids: tuple[str, ...]
    artifacts: tuple[ShapeBackfillArtifact, ...]


def build_shapes_api_url(
    api_key: str,
    *,
    operator_id: str,
    trip_id: str,
    base_url: str = DEFAULT_511_SHAPES_URL,
) -> str:
    query = urlencode(
        {
            "api_key": api_key,
            "operator_id": operator_id,
            "trip_id": trip_id,
            "format": "json",
        }
    )
    return f"{base_url}?{query}"


def normalize_trip_id_for_shapes_api(trip_id: str, *, operator_id: str) -> str:
    normalized = trip_id.strip()
    prefix = f"{operator_id}:"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):]
    parts = normalized.split(":")
    if len(parts) >= 2 and len(parts[-1]) == 8 and parts[-1].isdigit():
        normalized = ":".join(parts[:-1])
    return normalized


def _cache_key(shape_id: str, operator_id: str) -> str:
    digest = hashlib.sha256(
        f"{operator_id}\0{shape_id}".encode("utf-8")
    ).hexdigest()[:16]
    return digest


def _cache_path(
    cache_root: Path,
    *,
    shape_id: str,
    operator_id: str,
) -> Path:
    return cache_root / f"shape_backfill_{_cache_key(shape_id, operator_id)}.json"


def _iter_service_journeys(payload: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    content = payload.get("Content")
    if not isinstance(content, dict):
        return []

    timetable_frame = content.get("TimetableFrame")
    frames = timetable_frame if isinstance(timetable_frame, list) else [timetable_frame]
    journeys: list[dict[str, Any]] = []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        vehicle_journeys = frame.get("vehicleJourneys")
        if not isinstance(vehicle_journeys, dict):
            continue
        service_journey = vehicle_journeys.get("ServiceJourney")
        candidates = service_journey if isinstance(service_journey, list) else [service_journey]
        for candidate in candidates:
            if isinstance(candidate, dict):
                journeys.append(candidate)
    return journeys


def parse_shapes_api_positions(payload: Any) -> tuple[tuple[str, str], ...]:
    for journey in _iter_service_journeys(payload):
        projection = journey.get("LinkSequenceProjection")
        projections = projection if isinstance(projection, list) else [projection]
        for candidate in projections:
            if not isinstance(candidate, dict):
                continue
            line_string = candidate.get("LineString")
            if not isinstance(line_string, dict):
                continue
            positions = line_string.get("pos")
            if not isinstance(positions, list):
                continue
            normalized: list[tuple[str, str]] = []
            for index, raw_position in enumerate(positions, start=1):
                if not isinstance(raw_position, str):
                    raise ValueError(f"Shapes API position #{index} is not a string.")
                parts = raw_position.strip().split()
                if len(parts) != 2:
                    raise ValueError(
                        f"Shapes API position #{index} must contain latitude and longitude."
                    )
                latitude_text, longitude_text = parts
                float(latitude_text)
                float(longitude_text)
                normalized.append((latitude_text, longitude_text))
            if normalized:
                return tuple(normalized)

    raise ValueError("Shapes API response did not contain a usable LineString.pos geometry.")


def _load_cached_artifact(
    cache_path: Path,
    *,
    shape_id: str,
    operator_id: str,
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    if not cache_path.exists():
        return None

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    if (
        payload.get("shape_id") != shape_id
        or payload.get("operator_id") != operator_id
    ):
        return None

    positions = payload.get("positions")
    if not isinstance(positions, list) or not positions:
        return None

    cached_shapes_api_trip_id = payload.get("shapes_api_trip_id")
    if not isinstance(cached_shapes_api_trip_id, str) or not cached_shapes_api_trip_id:
        return None

    normalized: list[tuple[str, str]] = []
    for item in positions:
        if not isinstance(item, dict):
            return None
        latitude_text = item.get("shape_pt_lat")
        longitude_text = item.get("shape_pt_lon")
        if not isinstance(latitude_text, str) or not isinstance(longitude_text, str):
            return None
        normalized.append((latitude_text, longitude_text))
    return cached_shapes_api_trip_id, tuple(normalized)


def _load_cached_positions_from_payload(
    payload: Any,
    *,
    operator_id: str,
) -> tuple[str, tuple[tuple[str, str], ...]] | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("operator_id") != operator_id:
        return None

    positions = payload.get("positions")
    if not isinstance(positions, list) or not positions:
        return None

    cached_shapes_api_trip_id = payload.get("shapes_api_trip_id")
    if not isinstance(cached_shapes_api_trip_id, str) or not cached_shapes_api_trip_id:
        return None

    normalized: list[tuple[str, str]] = []
    for item in positions:
        if not isinstance(item, dict):
            return None
        latitude_text = item.get("shape_pt_lat")
        longitude_text = item.get("shape_pt_lon")
        if not isinstance(latitude_text, str) or not isinstance(longitude_text, str):
            return None
        normalized.append((latitude_text, longitude_text))
    return cached_shapes_api_trip_id, tuple(normalized)


def _index_cached_artifacts_by_trip_id(
    cache_root: Path,
    *,
    operator_id: str,
) -> dict[str, tuple[tuple[str, str], ...]]:
    indexed: dict[str, tuple[tuple[str, str], ...]] = {}
    if not cache_root.exists():
        return indexed
    for cache_path in cache_root.glob("shape_backfill_*.json"):
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        loaded = _load_cached_positions_from_payload(payload, operator_id=operator_id)
        if loaded is None:
            continue
        shapes_api_trip_id, positions = loaded
        indexed.setdefault(shapes_api_trip_id, positions)
    return indexed


def _write_cached_artifact(
    cache_path: Path,
    *,
    shape_id: str,
    representative_trip_id: str,
    shapes_api_trip_id: str,
    operator_id: str,
    requested_url: str,
    fetched_at: str,
    positions: tuple[tuple[str, str], ...],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "shape_id": shape_id,
        "representative_trip_id": representative_trip_id,
        "shapes_api_trip_id": shapes_api_trip_id,
        "operator_id": operator_id,
        "requested_url": requested_url,
        "fetched_at": fetched_at,
        "position_count": len(positions),
        "positions": [
            {
                "shape_pt_lat": latitude_text,
                "shape_pt_lon": longitude_text,
                "shape_pt_sequence": index,
            }
            for index, (latitude_text, longitude_text) in enumerate(positions, start=1)
        ],
    }
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def backfill_missing_shapes(
    shape_id_to_trip_ids: dict[str, str | list[str] | tuple[str, ...]],
    *,
    api_key: str,
    operator_id: str,
    cache_root: Path,
    timeout_seconds: int = 60,
    retry_attempts: int = 3,
    retry_backoff_seconds: float = 5.0,
) -> ShapeBackfillResult:
    shape_rows: list[dict[str, str]] = []
    request_count = 0
    cache_hit_count = 0
    successful_shape_count = 0
    failure_shape_ids: list[str] = []
    artifacts: list[ShapeBackfillArtifact] = []
    cached_positions_by_shapes_api_trip_id = _index_cached_artifacts_by_trip_id(
        cache_root,
        operator_id=operator_id,
    )

    for shape_id in sorted(shape_id_to_trip_ids):
        raw_candidates = shape_id_to_trip_ids[shape_id]
        if isinstance(raw_candidates, str):
            candidate_trip_ids = [raw_candidates]
        else:
            candidate_trip_ids = [candidate for candidate in raw_candidates if candidate]
        representative_trip_id = candidate_trip_ids[0]
        cache_path = _cache_path(
            cache_root,
            shape_id=shape_id,
            operator_id=operator_id,
        )
        cached_payload = _load_cached_artifact(
            cache_path,
            shape_id=shape_id,
            operator_id=operator_id,
        )
        positions = None
        shapes_api_trip_id = ""
        if cached_payload is not None:
            shapes_api_trip_id, positions = cached_payload
        requested_url = build_shapes_api_url(
            api_key,
            operator_id=operator_id,
            trip_id=shapes_api_trip_id,
        ) if shapes_api_trip_id else ""
        reused_cached = cached_payload is not None
        fetched_at = datetime.now(tz=UTC).isoformat()

        if positions is None:
            deduped_shapes_api_candidates: list[str] = []
            for trip_id in candidate_trip_ids:
                normalized_trip_id = normalize_trip_id_for_shapes_api(
                    trip_id,
                    operator_id=operator_id,
                )
                if normalized_trip_id and normalized_trip_id not in deduped_shapes_api_candidates:
                    deduped_shapes_api_candidates.append(normalized_trip_id)
            for candidate_shapes_api_trip_id in deduped_shapes_api_candidates:
                cached_positions = cached_positions_by_shapes_api_trip_id.get(
                    candidate_shapes_api_trip_id
                )
                if cached_positions is None:
                    continue
                shapes_api_trip_id = candidate_shapes_api_trip_id
                positions = cached_positions
                requested_url = build_shapes_api_url(
                    api_key,
                    operator_id=operator_id,
                    trip_id=candidate_shapes_api_trip_id,
                )
                reused_cached = True
                break
        if positions is None:
            success = False
            for candidate_shapes_api_trip_id in deduped_shapes_api_candidates:
                for attempt_index in range(retry_attempts):
                    request_count += 1
                    requested_url = build_shapes_api_url(
                        api_key,
                        operator_id=operator_id,
                        trip_id=candidate_shapes_api_trip_id,
                    )
                    request = Request(
                        requested_url,
                        headers={"User-Agent": "muni-lost-time-atlas/0.1"},
                    )
                    try:
                        with urlopen(request, timeout=timeout_seconds) as response:
                            payload = json.loads(response.read().decode("utf-8-sig"))
                        positions = parse_shapes_api_positions(payload)
                        shapes_api_trip_id = candidate_shapes_api_trip_id
                        success = True
                        break
                    except HTTPError as exc:
                        if (
                            exc.code == 429 or 500 <= exc.code < 600
                        ) and attempt_index + 1 < retry_attempts:
                            time.sleep(retry_backoff_seconds * (2 ** attempt_index))
                            continue
                    except Exception:
                        pass
                    break
                if success:
                    break
            if not success:
                failure_shape_ids.append(shape_id)
                continue
            _write_cached_artifact(
                cache_path,
                shape_id=shape_id,
                representative_trip_id=representative_trip_id,
                shapes_api_trip_id=shapes_api_trip_id,
                operator_id=operator_id,
                requested_url=requested_url,
                fetched_at=fetched_at,
                positions=positions,
            )
            cached_positions_by_shapes_api_trip_id[shapes_api_trip_id] = positions
        else:
            cache_hit_count += 1

        successful_shape_count += 1
        artifacts.append(
            ShapeBackfillArtifact(
                shape_id=shape_id,
                representative_trip_id=representative_trip_id,
                shapes_api_trip_id=shapes_api_trip_id,
                cache_path=cache_path,
                point_count=len(positions),
                reused_cached=reused_cached,
                fetched_at=fetched_at,
                requested_url=requested_url,
            )
        )
        for index, (latitude_text, longitude_text) in enumerate(positions, start=1):
            shape_rows.append(
                {
                    "shape_id": shape_id,
                    "shape_pt_lat": latitude_text,
                    "shape_pt_lon": longitude_text,
                    "shape_pt_sequence": str(index),
                    "shape_dist_traveled": "",
                }
            )

    return ShapeBackfillResult(
        shape_rows=tuple(shape_rows),
        request_count=request_count,
        cache_hit_count=cache_hit_count,
        successful_shape_count=successful_shape_count,
        failure_shape_ids=tuple(failure_shape_ids),
        artifacts=tuple(artifacts),
    )
