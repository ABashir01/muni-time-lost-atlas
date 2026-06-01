from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.transit_lane_overlay_fixture_ingest import get_default_fixture_path


class TransitLaneOverlayFixtureIngestTests(unittest.TestCase):
    def test_get_default_fixture_path_honors_fixtures_root_env(self) -> None:
        with patch.dict(os.environ, {"FIXTURES_ROOT": "/app/fixtures"}, clear=False):
            self.assertEqual(
                get_default_fixture_path(),
                Path("/app/fixtures/geospatial/transit_only_lanes/minimal.geojson"),
            )


if __name__ == "__main__":
    unittest.main()
