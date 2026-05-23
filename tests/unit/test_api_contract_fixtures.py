"""Contract checks for committed API fixture payloads."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src_dir = root / "api" / "src"
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_api.models import (  # noqa: E402
    CompareResponse,
    HealthResponse,
    MapRoutesResponse,
    RankingsResponse,
    RouteStopWaitResponse,
    RouteSegmentsResponse,
    RouteSummary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
API_FIXTURE_DIR = REPO_ROOT / "fixtures" / "api"


class ApiContractFixtureTests(unittest.TestCase):
    def test_committed_api_fixtures_match_response_models(self) -> None:
        fixture_models = {
            "health.json": HealthResponse,
            "rankings_all_day_typical_trip_loss_minutes_routes.json": RankingsResponse,
            "route_14_summary_all_day.json": RouteSummary,
            "route_14_segments_direction_1_all_day.json": RouteSegmentsResponse,
            "route_14_stops_wait_direction_1_all_day.json": RouteStopWaitResponse,
            "routes_compare_14_49_all_day.json": CompareResponse,
            "map_routes_all_day_typical_trip_loss_minutes.json": MapRoutesResponse,
        }

        for fixture_name, model in fixture_models.items():
            fixture_path = API_FIXTURE_DIR / fixture_name
            with self.subTest(fixture=fixture_name):
                payload = json.loads(fixture_path.read_text(encoding="utf-8"))
                validated = model.model_validate(payload)
                self.assertEqual(
                    validated.model_dump(mode="json", exclude_none=True),
                    payload,
                )


if __name__ == "__main__":
    unittest.main()
