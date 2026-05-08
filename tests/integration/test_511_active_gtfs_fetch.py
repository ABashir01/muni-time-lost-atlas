"""Controlled integration checks for active 511 GTFS acquisition."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src_dir = root / "pipeline" / "src"
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.active_gtfs_fetch import (  # noqa: E402
    fetch_active_gtfs_archive,
    get_511_api_key,
)


class ActiveGtfsFetchIntegrationTests(unittest.TestCase):
    def test_live_511_fetch_if_token_is_configured(self) -> None:
        try:
            api_key = get_511_api_key()
        except ValueError as exc:
            self.skipTest(str(exc))

        if api_key == "replace_with_local_511_token":
            self.skipTest("TRANSIT_511_API_KEY is still the placeholder example value.")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                result = fetch_active_gtfs_archive(
                    api_key=api_key,
                    acquisitions_root=Path(tmpdir),
                    timeout_seconds=60,
                )
            except URLError as exc:
                self.skipTest(f"Network access to 511 is not available in this environment: {exc}")

            self.assertTrue(result.artifact_path.exists())
            self.assertTrue(result.metadata_path.exists())
            metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_system"], "511")
            self.assertEqual(metadata["feed_scope"], "operator_active")
            self.assertEqual(metadata["operator_id"], "SF")
            self.assertIn("operator_id=SF", metadata["requested_url"])
