"""Integration tests for the B6a real dataset cutover bundle."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest
from urllib.parse import quote

from fastapi.testclient import TestClient


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_api.app import create_app  # noqa: E402
from muni_lta_pipeline.active_gtfs_fetch import get_511_api_key  # noqa: E402
from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    get_postgres_settings,
    run_psql_sql,
)
from muni_lta_pipeline.real_dataset_cutover import (  # noqa: E402
    DEFAULT_CUTOVER_ROOT,
    DEFAULT_HISTORIC_AGENCY_ID,
    DEFAULT_HISTORIC_MONTH,
    materialize_real_dataset_cutover,
)


def _resolve_metadata_paths_from_latest_manifest() -> tuple[Path, Path] | None:
    latest_manifest_path = DEFAULT_CUTOVER_ROOT / "latest.json"
    if not latest_manifest_path.exists():
        return None

    manifest = json.loads(latest_manifest_path.read_text(encoding="utf-8"))
    active_metadata_path = Path(manifest["active_gtfs_metadata_path"])
    historic_metadata_path = Path(manifest["historic_gtfs_metadata_path"])
    if not active_metadata_path.exists() or not historic_metadata_path.exists():
        return None

    return active_metadata_path, historic_metadata_path


class RealDatasetCutoverBundleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        metadata_paths = _resolve_metadata_paths_from_latest_manifest()
        if metadata_paths is None:
            try:
                api_key = get_511_api_key()
            except ValueError as exc:
                raise unittest.SkipTest(str(exc)) from exc

            if api_key == "replace_with_local_511_token":
                raise unittest.SkipTest(
                    "TRANSIT_511_API_KEY is still the placeholder example value."
                )

        active_metadata_path = historic_metadata_path = None
        if metadata_paths is not None:
            active_metadata_path, historic_metadata_path = metadata_paths

        cls.result = materialize_real_dataset_cutover(
            historic_month=DEFAULT_HISTORIC_MONTH,
            historic_agency_id=DEFAULT_HISTORIC_AGENCY_ID,
            active_metadata_path=active_metadata_path,
            historic_metadata_path=historic_metadata_path,
        )
        cls.repeat_result = materialize_real_dataset_cutover(
            historic_month=DEFAULT_HISTORIC_MONTH,
            historic_agency_id=DEFAULT_HISTORIC_AGENCY_ID,
            active_metadata_path=cls.result.active_gtfs_metadata_path,
            historic_metadata_path=cls.result.historic_gtfs_metadata_path,
        )
        cls.settings = get_postgres_settings()
        cls.client = TestClient(create_app())

    def test_real_cutover_build_materializes_a_broad_route_set(self) -> None:
        self.assertGreaterEqual(self.result.route_count_with_metrics, 20)
        self.assertGreaterEqual(self.result.map_route_count, 20)
        self.assertGreaterEqual(len(self.result.top_route_ids), 5)
        self.assertTrue(
            any(route_id not in {"SF:14", "SF:49"} for route_id in self.result.top_route_ids)
        )

        route_rows = run_psql_sql(
            self.settings,
            """
            SELECT route_id
            FROM marts.route_window_summary
            WHERE typical_trip_loss_minutes IS NOT NULL
            ORDER BY typical_trip_loss_minutes DESC NULLS LAST, route_id
            LIMIT 25;
            """,
        ).splitlines()
        self.assertGreaterEqual(len(route_rows), 20)
        self.assertIn("SF:14", route_rows)
        self.assertIn("SF:49", route_rows)

    def test_api_contract_reads_from_the_real_cutover_dataset(self) -> None:
        rankings_response = self.client.get(
            "/rankings",
            params={"window": "all_day", "metric": "typical_trip_loss_minutes"},
        )
        self.assertEqual(rankings_response.status_code, 200)
        rankings_payload = rankings_response.json()
        self.assertEqual(rankings_payload["window"], "all_day")
        self.assertEqual(rankings_payload["metric"], "typical_trip_loss_minutes")
        self.assertGreaterEqual(len(rankings_payload["routes"]), 20)

        top_route_ids = [
            route["route_id"] for route in rankings_payload["routes"][:2]
        ]
        compare_response = self.client.get(
            "/routes/compare",
            params={"ids": ",".join(top_route_ids), "window": "all_day"},
        )
        self.assertEqual(compare_response.status_code, 200)
        self.assertEqual(compare_response.json()["route_ids"], top_route_ids)

        summary_response = self.client.get(
            f"/routes/{quote(top_route_ids[0], safe='')}/summary",
            params={"window": "all_day"},
        )
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.json()["route_id"], top_route_ids[0])

        map_response = self.client.get(
            "/map/routes",
            params={"window": "all_day", "metric": "typical_trip_loss_minutes"},
        )
        self.assertEqual(map_response.status_code, 200)
        self.assertGreaterEqual(len(map_response.json()["features"]), 20)

    def test_repeat_cutover_reuses_matching_dbt_manifest(self) -> None:
        self.assertTrue(self.repeat_result.reused_existing_dbt)
        self.assertTrue(self.repeat_result.skipped_dbt)
        self.assertEqual(self.repeat_result.dbt_action, "reused_existing")


if __name__ == "__main__":
    unittest.main()
