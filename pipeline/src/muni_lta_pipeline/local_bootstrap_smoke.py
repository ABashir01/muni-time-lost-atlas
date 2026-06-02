"""Container-friendly offline smoke test for the publisher bootstrap path."""

from __future__ import annotations

import csv
from datetime import datetime
import json
from pathlib import Path
import tempfile
import zipfile

from muni_lta_pipeline.config import get_pipeline_settings
from muni_lta_pipeline.real_dataset_cutover import (
    materialize_prepared_historic_publication,
)


SETTINGS = get_pipeline_settings()
FIXTURES_ROOT = SETTINGS.fixtures_root
GTFS_FIXTURE_DIR = FIXTURES_ROOT / "gtfs_static" / "metrics_core"
OBS_FIXTURE_PATH = (
    FIXTURES_ROOT / "stop_observations" / "regional_rg_metrics_core" / "stop_observations.txt"
)


def _write_active_archive(output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    artifact_path = output_root / "fixture_operator_active_SF_20260501T000000Z.zip"
    metadata_path = output_root / "fixture_operator_active_SF_20260501T000000Z.json"

    with zipfile.ZipFile(artifact_path, mode="w") as archive:
        for fixture_path in sorted(GTFS_FIXTURE_DIR.iterdir()):
            archive.write(fixture_path, arcname=fixture_path.name)

    metadata_path.write_text(
        json.dumps(
            {
                "source_system": "fixture",
                "feed_scope": "operator_active",
                "operator_id": "SF",
                "requested_url": "fixture://operator_active",
                "fetched_at": "2026-05-01T00:00:00+00:00",
                "artifact_filename": artifact_path.name,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return metadata_path


def _build_historic_stop_observations_csv() -> str:
    rows: list[dict[str, str]] = []
    with OBS_FIXTURE_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            observed_arrival = datetime.fromisoformat(
                raw_row["observed_arrival_time"].strip()
            ).strftime("%H:%M:%S")
            rows.append(
                {
                    "service_date": raw_row["service_date"].replace("-", "").strip(),
                    "trip_id": raw_row["trip_id"].strip(),
                    "stop_sequence": raw_row["stop_sequence"].strip(),
                    "to_stop_id": raw_row["stop_id"].strip(),
                    "observed_arrival_time": observed_arrival,
                }
            )

    lines = ["service_date,trip_id,stop_sequence,to_stop_id,observed_arrival_time"]
    for row in rows:
        lines.append(
            ",".join(
                [
                    row["service_date"],
                    row["trip_id"],
                    row["stop_sequence"],
                    row["to_stop_id"],
                    row["observed_arrival_time"],
                ]
            )
        )
    return "\n".join(lines) + "\n"


def _write_historic_publication_archive(output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    artifact_path = (
        output_root
        / "fixture_regional_historic_sf_publication_SF_202605_window3.zip"
    )
    metadata_path = (
        output_root
        / "fixture_regional_historic_sf_publication_SF_202605_window3.json"
    )

    with zipfile.ZipFile(artifact_path, mode="w") as archive:
        for fixture_path in sorted(GTFS_FIXTURE_DIR.iterdir()):
            archive.write(fixture_path, arcname=fixture_path.name)
        archive.writestr("stop_observations.txt", _build_historic_stop_observations_csv())

    metadata_path.write_text(
        json.dumps(
            {
                "source_system": "fixture",
                "feed_scope": "regional_historic_sf_publication",
                "operator_id": "SF",
                "requested_historic_month": "2026-05",
                "requested_historic_value": "2026-05-so",
                "requested_stop_observations": True,
                "requested_url": "fixture://regional_historic_sf_publication",
                "fetched_at": "2026-05-01T00:00:00+00:00",
                "artifact_filename": artifact_path.name,
                "stop_observations_present": True,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return metadata_path


def main() -> int:
    smoke_root = Path("/app/artifacts/smoke")
    smoke_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="publisher_bootstrap_", dir=smoke_root) as tmpdir:
        scenario_root = Path(tmpdir)
        active_metadata_path = _write_active_archive(scenario_root / "active")
        historic_metadata_path = _write_historic_publication_archive(
            scenario_root / "historic_publication"
        )
        cutover_root = scenario_root / "cutover"
        latest_log_path = cutover_root / "latest.log"

        result = materialize_prepared_historic_publication(
            active_metadata_path=active_metadata_path,
            historic_source_metadata_path=historic_metadata_path,
            historic_gtfs_metadata_path=historic_metadata_path,
            historic_feed_scope="regional_historic_sf_publication",
            historic_month="2026-05",
            historic_agency_id="SF",
            cutover_root=cutover_root,
            log_path=cutover_root / "first.log",
            latest_log_path=latest_log_path,
        )
        repeat_result = materialize_prepared_historic_publication(
            active_metadata_path=active_metadata_path,
            historic_source_metadata_path=historic_metadata_path,
            historic_gtfs_metadata_path=historic_metadata_path,
            historic_feed_scope="regional_historic_sf_publication",
            historic_month="2026-05",
            historic_agency_id="SF",
            cutover_root=cutover_root,
            log_path=cutover_root / "repeat.log",
            latest_log_path=latest_log_path,
        )

        if result.route_count_with_metrics <= 0:
            raise RuntimeError("Publisher smoke produced no route metrics.")
        if result.map_route_count <= 0:
            raise RuntimeError("Publisher smoke produced no map routes.")
        if not repeat_result.reused_existing_gtfs_raw:
            raise RuntimeError("Publisher smoke did not reuse raw GTFS on rerun.")
        if not repeat_result.reused_existing_observed_raw:
            raise RuntimeError("Publisher smoke did not reuse raw stop observations on rerun.")
        if not repeat_result.reused_existing_overlay_raw:
            raise RuntimeError("Publisher smoke did not reuse overlay raw data on rerun.")
        if not repeat_result.reused_existing_dbt or repeat_result.dbt_action != "reused_existing":
            raise RuntimeError("Publisher smoke did not reuse dbt outputs on rerun.")

        print(
            json.dumps(
                {
                    "status": "ok",
                    "route_count_with_metrics": result.route_count_with_metrics,
                    "map_route_count": result.map_route_count,
                    "top_route_ids": result.top_route_ids,
                    "manifest_path": str(result.manifest_path),
                    "reused_existing_dbt_on_repeat": repeat_result.reused_existing_dbt,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
