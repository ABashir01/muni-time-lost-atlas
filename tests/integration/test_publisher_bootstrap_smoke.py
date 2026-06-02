"""Local smoke test for the publisher bootstrap cutover path.

This test avoids live 511 calls by building synthetic archive metadata and zip
artifacts from committed fixtures, then running the real publication cutover.
"""

from __future__ import annotations

import csv
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("APP_ROOT", str(REPO_ROOT))
os.environ.setdefault("FIXTURES_ROOT", str(REPO_ROOT / "fixtures"))


def _configure_src_paths() -> None:
    for src_dir in (REPO_ROOT / "api" / "src", REPO_ROOT / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.real_dataset_cutover import (  # noqa: E402
    materialize_prepared_historic_publication,
)


GTFS_FIXTURE_DIR = REPO_ROOT / "fixtures" / "gtfs_static" / "metrics_core"
OBS_FIXTURE_PATH = (
    REPO_ROOT
    / "fixtures"
    / "stop_observations"
    / "regional_rg_metrics_core"
    / "stop_observations.txt"
)
WORKSPACE_TMP_ROOT = REPO_ROOT / ".tmp"
SCENARIO_ROOT = WORKSPACE_TMP_ROOT / "publisher_bootstrap_smoke"


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
        archive.writestr(
            "stop_observations.txt",
            _build_historic_stop_observations_csv(),
        )

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


class PublisherBootstrapSmokeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        WORKSPACE_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(SCENARIO_ROOT, ignore_errors=True)
        SCENARIO_ROOT.mkdir(parents=True, exist_ok=True)

        cls.active_metadata_path = _write_active_archive(SCENARIO_ROOT / "active")
        cls.historic_metadata_path = _write_historic_publication_archive(
            SCENARIO_ROOT / "historic_publication"
        )
        cls.cutover_root = SCENARIO_ROOT / "cutover"
        cls.log_path = cls.cutover_root / "latest-run.log"
        cls.latest_log_path = cls.cutover_root / "latest.log"

        cls.result = materialize_prepared_historic_publication(
            active_metadata_path=cls.active_metadata_path,
            historic_source_metadata_path=cls.historic_metadata_path,
            historic_gtfs_metadata_path=cls.historic_metadata_path,
            historic_feed_scope="regional_historic_sf_publication",
            historic_month="2026-05",
            historic_agency_id="SF",
            cutover_root=cls.cutover_root,
            log_path=cls.log_path,
            latest_log_path=cls.latest_log_path,
        )
        cls.repeat_result = materialize_prepared_historic_publication(
            active_metadata_path=cls.active_metadata_path,
            historic_source_metadata_path=cls.historic_metadata_path,
            historic_gtfs_metadata_path=cls.historic_metadata_path,
            historic_feed_scope="regional_historic_sf_publication",
            historic_month="2026-05",
            historic_agency_id="SF",
            cutover_root=cls.cutover_root,
            log_path=cls.cutover_root / "repeat.log",
            latest_log_path=cls.latest_log_path,
        )

    def test_smoke_cutover_materializes_manifest_and_logs(self) -> None:
        self.assertTrue(self.result.manifest_path.exists())
        self.assertTrue(self.result.latest_manifest_path.exists())
        self.assertTrue(self.result.log_path.exists())
        self.assertTrue(self.result.latest_log_path.exists())

    def test_smoke_cutover_builds_app_facing_rows(self) -> None:
        self.assertGreater(self.result.route_count_with_metrics, 0)
        self.assertGreater(self.result.map_route_count, 0)
        self.assertGreater(len(self.result.top_route_ids), 0)

    def test_repeat_smoke_cutover_reuses_raw_and_dbt(self) -> None:
        self.assertTrue(self.repeat_result.reused_existing_gtfs_raw)
        self.assertTrue(self.repeat_result.reused_existing_observed_raw)
        self.assertTrue(self.repeat_result.reused_existing_overlay_raw)
        self.assertTrue(self.repeat_result.reused_existing_dbt)
        self.assertTrue(self.repeat_result.skipped_dbt)
        self.assertEqual(self.repeat_result.dbt_action, "reused_existing")


if __name__ == "__main__":
    unittest.main()
