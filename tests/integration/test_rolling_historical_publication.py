"""Light integration checks for B7 rolling historical publication helpers."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest
from urllib.error import URLError


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src_dir = root / "pipeline" / "src"
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.active_gtfs_fetch import get_511_api_key  # noqa: E402
from muni_lta_pipeline.rolling_historical_publication import (  # noqa: E402
    check_newest_available_completed_month,
)


class RollingHistoricalPublicationIntegrationTests(unittest.TestCase):
    def test_live_511_availability_probe_for_recent_completed_month_if_token_is_configured(self) -> None:
        try:
            api_key = get_511_api_key()
        except ValueError as exc:
            self.skipTest(str(exc))

        if api_key == "replace_with_local_511_token":
            self.skipTest("TRANSIT_511_API_KEY is still the placeholder example value.")

        try:
            result = check_newest_available_completed_month(
                api_key=api_key,
                current_date=date(2026, 5, 24),
            )
        except URLError as exc:
            self.skipTest(f"Network access to 511 is not available in this environment: {exc}")

        self.assertEqual(result.historic_month, "2026-04")
        self.assertTrue(result.available)


if __name__ == "__main__":
    unittest.main()
