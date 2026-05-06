"""Bootstrap tests for the Python project foundation slice."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_api import __version__ as api_version  # noqa: E402
from muni_lta_api.config import ApiSettings, get_api_settings  # noqa: E402
from muni_lta_api.app import create_app  # noqa: E402
from muni_lta_pipeline import __version__ as pipeline_version  # noqa: E402
from muni_lta_pipeline.config import (  # noqa: E402
    PipelineSettings,
    get_pipeline_settings,
)


class PythonBootstrapTests(unittest.TestCase):
    def test_placeholder_unit_test(self) -> None:
        self.assertTrue(True)

    def test_import_smoke_for_api_and_pipeline_packages(self) -> None:
        self.assertEqual(api_version, "0.1.0")
        self.assertEqual(pipeline_version, "0.1.0")
        self.assertIsInstance(get_api_settings({}), ApiSettings)
        self.assertIsInstance(get_pipeline_settings({}), PipelineSettings)
        self.assertTrue(callable(create_app))
