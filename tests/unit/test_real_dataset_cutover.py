"""Unit tests for manifest-aware real dataset cutover reuse."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.real_dataset_cutover import (  # noqa: E402
    _compute_dbt_fingerprint,
    _compute_raw_input_fingerprint,
    _find_reusable_dbt_manifest,
    materialize_real_dataset_cutover,
)


class _FakeCursor:
    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str) -> None:
        self.sql = sql

    def fetchall(self) -> list[tuple[str]]:
        return [("SF:49",), ("SF:F",), ("SF:14",)]


class _FakeConnection:
    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return _FakeCursor()


class RealDatasetCutoverUnitTests(unittest.TestCase):
    def test_compute_dbt_fingerprint_tracks_dbt_files_and_vars(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        repo_root = workspace_tmp_root / "real_dataset_cutover_fingerprint"
        shutil.rmtree(repo_root, ignore_errors=True)
        (repo_root / "dbt" / "models").mkdir(parents=True, exist_ok=True)
        (repo_root / "dbt" / "macros").mkdir(parents=True, exist_ok=True)

        try:
            (repo_root / "dbt_project.yml").write_text("name: test_project\n", encoding="utf-8")
            (repo_root / "dbt" / "models" / "a.sql").write_text("select 1 as value\n", encoding="utf-8")
            (repo_root / "dbt" / "macros" / "b.sql").write_text("{% macro demo() %}1{% endmacro %}\n", encoding="utf-8")
            (repo_root / "notes.txt").write_text("ignored\n", encoding="utf-8")

            baseline = _compute_dbt_fingerprint({"historic_agency_id": "SF"}, repo_root=repo_root)
            repeat = _compute_dbt_fingerprint({"historic_agency_id": "SF"}, repo_root=repo_root)
            changed_vars = _compute_dbt_fingerprint({"historic_agency_id": "AC"}, repo_root=repo_root)

            self.assertEqual(baseline["sha256"], repeat["sha256"])
            self.assertEqual(
                baseline["tracked_paths"],
                ["dbt/macros/b.sql", "dbt/models/a.sql", "dbt_project.yml"],
            )
            self.assertNotEqual(baseline["sha256"], changed_vars["sha256"])

            (repo_root / "dbt" / "models" / "a.sql").write_text("select 2 as value\n", encoding="utf-8")
            changed_model = _compute_dbt_fingerprint(
                {"historic_agency_id": "SF"},
                repo_root=repo_root,
            )
            self.assertNotEqual(baseline["sha256"], changed_model["sha256"])
        finally:
            shutil.rmtree(repo_root, ignore_errors=True)

    def test_find_reusable_dbt_manifest_ignores_requested_skip_and_uses_last_successful(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        cutover_root = workspace_tmp_root / "real_dataset_cutover_manifest_search"
        shutil.rmtree(cutover_root, ignore_errors=True)
        cutover_root.mkdir(parents=True, exist_ok=True)

        raw_snapshot_labels = {
            "active_gtfs_snapshot_label": "active_a",
            "historic_gtfs_snapshot_label": "historic_a",
            "historic_observed_snapshot_label": "observed_a",
            "overlay_snapshot_label": "overlay_a",
        }
        dbt_vars = {"historic_agency_id": "SF"}
        dbt_fingerprint = {"sha256": "fingerprint_a", "tracked_paths": ["dbt/models/a.sql"]}
        raw_input_fingerprint = {"sha256": "raw_fingerprint_a", "tracked_inputs": ["active.json", "historic.json"]}

        try:
            successful_manifest_path = cutover_root / "20260521T120000Z.json"
            successful_manifest_path.write_text(
                json.dumps(
                    {
                        "dbt_action": "run",
                        "dbt_fingerprint": dbt_fingerprint,
                        "dbt_vars": dbt_vars,
                        "manifest_path": str(successful_manifest_path),
                        "raw_input_fingerprint": raw_input_fingerprint,
                        "raw_snapshot_labels": raw_snapshot_labels,
                        "skipped_dbt": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (cutover_root / "latest.json").write_text(
                json.dumps(
                    {
                        "dbt_action": "skipped_by_request",
                        "dbt_fingerprint": dbt_fingerprint,
                        "dbt_vars": dbt_vars,
                        "manifest_path": str(cutover_root / "latest.json"),
                        "raw_input_fingerprint": raw_input_fingerprint,
                        "raw_snapshot_labels": raw_snapshot_labels,
                        "skipped_dbt": True,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            reusable = _find_reusable_dbt_manifest(
                cutover_root=cutover_root,
                raw_snapshot_labels=raw_snapshot_labels,
                raw_input_fingerprint=raw_input_fingerprint,
                dbt_vars=dbt_vars,
                dbt_fingerprint=dbt_fingerprint,
            )

            self.assertIsNotNone(reusable)
            assert reusable is not None
            self.assertEqual(reusable[0], successful_manifest_path)
        finally:
            shutil.rmtree(cutover_root, ignore_errors=True)

    def test_materialize_real_dataset_cutover_skips_dbt_when_manifest_matches(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        scenario_root = workspace_tmp_root / "real_dataset_cutover_skip_dbt"
        shutil.rmtree(scenario_root, ignore_errors=True)
        scenario_root.mkdir(parents=True, exist_ok=True)

        active_metadata_path = scenario_root / "active.json"
        historic_metadata_path = scenario_root / "historic.json"
        cutover_root = scenario_root / "cutovers"
        cutover_root.mkdir(parents=True, exist_ok=True)

        active_metadata_path.write_text("{}", encoding="utf-8")
        historic_metadata_path.write_text("{}", encoding="utf-8")

        fingerprint = {"sha256": "fingerprint_a", "tracked_paths": ["dbt/models/a.sql"]}
        raw_input_fingerprint = {
            "sha256": "raw_fingerprint_a",
            "tracked_inputs": [str(active_metadata_path), str(historic_metadata_path), "overlay"],
        }
        prior_manifest_path = cutover_root / "20260521T120000Z.json"
        prior_manifest_path.write_text(
            json.dumps(
                {
                    "dbt_action": "run",
                    "dbt_fingerprint": fingerprint,
                    "dbt_reuse_manifest_path": None,
                    "dbt_vars": {
                        "gtfs_feed_scope": "regional_historic_sf",
                        "gtfs_snapshot_label": "historic_label",
                        "historic_agency_id": "SF",
                        "metrics_intermediate_materialization": "table",
                        "observed_canonical_materialization": "table",
                        "observed_feed_scope": "regional_historic_sf",
                        "observed_snapshot_label": "observed_label",
                        "performance_indexing": True,
                    },
                    "manifest_path": str(prior_manifest_path),
                    "raw_input_fingerprint": raw_input_fingerprint,
                    "raw_snapshot_labels": {
                        "active_gtfs_snapshot_label": "active_label",
                        "historic_gtfs_snapshot_label": "historic_label",
                        "historic_observed_snapshot_label": "observed_label",
                        "overlay_snapshot_label": "fixture_transit_lanes_v1",
                    },
                    "skipped_dbt": False,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        (cutover_root / "latest.json").write_text(
            prior_manifest_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        historic_extract_result = SimpleNamespace(
            metadata_path=historic_metadata_path,
            reused_existing=True,
            metadata=SimpleNamespace(
                feed_scope="regional_historic_sf",
                retained_row_counts={"routes.txt": 65},
            ),
        )

        def _fake_query_int(_connection: object, sql: str) -> int:
            if "route_window_summary" in sql:
                return 65
            if "route_map_layer" in sql:
                return 65
            return 0

        try:
            with (
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.extract_sf_historic_archive",
                    return_value=historic_extract_result,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.build_gtfs_archive_snapshot_label",
                    side_effect=["active_label", "historic_label"],
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.build_observed_archive_snapshot_label",
                    return_value="observed_label",
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.build_postgres_connection_url",
                    return_value="postgresql://example",
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._gtfs_snapshot_present",
                    return_value=True,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._stop_observations_snapshot_present",
                    return_value=True,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._overlay_snapshot_present",
                    return_value=True,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._snapshot_row_count",
                    return_value=2,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._compute_dbt_fingerprint",
                    return_value=fingerprint,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._compute_raw_input_fingerprint",
                    return_value=raw_input_fingerprint,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._query_int",
                    side_effect=_fake_query_int,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.psycopg.connect",
                    return_value=_FakeConnection(),
                ),
                patch("muni_lta_pipeline.real_dataset_cutover.run_dbt_run") as mock_run_dbt,
            ):
                result = materialize_real_dataset_cutover(
                    historic_month="2023-02",
                    historic_agency_id="SF",
                    active_metadata_path=active_metadata_path,
                    historic_metadata_path=historic_metadata_path,
                    cutover_root=cutover_root,
                )

            mock_run_dbt.assert_not_called()
            self.assertTrue(result.reused_existing_dbt)
            self.assertTrue(result.skipped_dbt)
            self.assertEqual(result.dbt_action, "reused_existing")

            latest_manifest = json.loads((cutover_root / "latest.json").read_text(encoding="utf-8"))
            self.assertTrue(latest_manifest["reused_existing_dbt"])
            self.assertTrue(latest_manifest["skipped_dbt"])
            self.assertEqual(latest_manifest["dbt_action"], "reused_existing")
            self.assertEqual(latest_manifest["dbt_reuse_manifest_path"], str(prior_manifest_path))
            self.assertEqual(latest_manifest["raw_input_fingerprint"], raw_input_fingerprint)
        finally:
            shutil.rmtree(scenario_root, ignore_errors=True)

    def test_materialize_real_dataset_cutover_does_not_reuse_raw_or_dbt_when_raw_input_fingerprint_changes(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        scenario_root = workspace_tmp_root / "real_dataset_cutover_input_fingerprint_change"
        shutil.rmtree(scenario_root, ignore_errors=True)
        scenario_root.mkdir(parents=True, exist_ok=True)

        active_metadata_path = scenario_root / "active.json"
        historic_metadata_path = scenario_root / "historic.json"
        cutover_root = scenario_root / "cutovers"
        cutover_root.mkdir(parents=True, exist_ok=True)

        active_metadata_path.write_text("{}", encoding="utf-8")
        historic_metadata_path.write_text("{}", encoding="utf-8")

        dbt_fingerprint = {"sha256": "fingerprint_a", "tracked_paths": ["dbt/models/a.sql"]}
        prior_raw_input_fingerprint = {
            "sha256": "raw_fingerprint_old",
            "tracked_inputs": [str(active_metadata_path), str(historic_metadata_path), "overlay"],
        }
        current_raw_input_fingerprint = {
            "sha256": "raw_fingerprint_new",
            "tracked_inputs": [str(active_metadata_path), str(historic_metadata_path), "overlay"],
        }
        prior_manifest_path = cutover_root / "20260521T120000Z.json"
        prior_manifest_path.write_text(
            json.dumps(
                {
                    "dbt_action": "run",
                    "dbt_fingerprint": dbt_fingerprint,
                    "dbt_vars": {
                        "gtfs_feed_scope": "regional_historic_sf",
                        "gtfs_snapshot_label": "historic_label",
                        "historic_agency_id": "SF",
                        "metrics_intermediate_materialization": "table",
                        "observed_canonical_materialization": "table",
                        "observed_feed_scope": "regional_historic_sf",
                        "observed_snapshot_label": "observed_label",
                        "performance_indexing": True,
                    },
                    "manifest_path": str(prior_manifest_path),
                    "raw_input_fingerprint": prior_raw_input_fingerprint,
                    "raw_snapshot_labels": {
                        "active_gtfs_snapshot_label": "active_label",
                        "historic_gtfs_snapshot_label": "historic_label",
                        "historic_observed_snapshot_label": "observed_label",
                        "overlay_snapshot_label": "fixture_transit_lanes_v1",
                    },
                    "skipped_dbt": False,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        (cutover_root / "latest.json").write_text(
            prior_manifest_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        historic_extract_result = SimpleNamespace(
            metadata_path=historic_metadata_path,
            reused_existing=False,
            metadata=SimpleNamespace(
                feed_scope="regional_historic_sf",
                retained_row_counts={"routes.txt": 65},
                shape_backfill_cache_hits=0,
                shape_backfill_failure_count=0,
                shape_backfill_manifest_path="",
                shape_backfill_request_count=0,
                shape_backfill_shape_count=0,
                shape_backfill_trip_selection_strategy="unique_active_shape_then_shapes_api",
                shape_fallback_used=False,
            ),
        )

        def _fake_query_int(_connection: object, sql: str) -> int:
            if "route_window_summary" in sql:
                return 65
            if "route_map_layer" in sql:
                return 65
            return 0

        try:
            with (
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.extract_sf_historic_archive",
                    return_value=historic_extract_result,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.build_gtfs_archive_snapshot_label",
                    side_effect=["active_label", "historic_label"],
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.build_observed_archive_snapshot_label",
                    return_value="observed_label",
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.build_postgres_connection_url",
                    return_value="postgresql://example",
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._gtfs_snapshot_present",
                    return_value=True,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._stop_observations_snapshot_present",
                    return_value=True,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._overlay_snapshot_present",
                    return_value=True,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._snapshot_row_count",
                    return_value=2,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._compute_dbt_fingerprint",
                    return_value=dbt_fingerprint,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._compute_raw_input_fingerprint",
                    return_value=current_raw_input_fingerprint,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover._query_int",
                    side_effect=_fake_query_int,
                ),
                patch(
                    "muni_lta_pipeline.real_dataset_cutover.psycopg.connect",
                    return_value=_FakeConnection(),
                ),
                patch("muni_lta_pipeline.real_dataset_cutover.load_gtfs_archive") as mock_load_gtfs,
                patch("muni_lta_pipeline.real_dataset_cutover.load_historic_stop_observations_archive") as mock_load_observed,
                patch("muni_lta_pipeline.real_dataset_cutover.load_transit_lane_overlay_fixture", return_value=2) as mock_load_overlay,
                patch("muni_lta_pipeline.real_dataset_cutover.run_dbt_run") as mock_run_dbt,
            ):
                mock_load_gtfs.side_effect = [
                    SimpleNamespace(snapshot_label="active_label", inserted_row_counts={}),
                    SimpleNamespace(snapshot_label="historic_label", inserted_row_counts={}),
                ]
                mock_load_observed.return_value = SimpleNamespace(
                    snapshot_label="observed_label",
                    inserted_row_count=0,
                    skipped_missing_required_count=0,
                )

                result = materialize_real_dataset_cutover(
                    historic_month="2023-02",
                    historic_agency_id="SF",
                    active_metadata_path=active_metadata_path,
                    historic_metadata_path=historic_metadata_path,
                    cutover_root=cutover_root,
                )

            self.assertFalse(result.reused_existing_gtfs_raw)
            self.assertFalse(result.reused_existing_observed_raw)
            self.assertFalse(result.reused_existing_overlay_raw)
            self.assertFalse(result.reused_existing_dbt)
            self.assertFalse(result.skipped_dbt)
            self.assertEqual(result.dbt_action, "run")
            self.assertEqual(mock_load_gtfs.call_count, 2)
            mock_load_observed.assert_called_once()
            mock_load_overlay.assert_called_once()
            mock_run_dbt.assert_called_once()
        finally:
            shutil.rmtree(scenario_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
