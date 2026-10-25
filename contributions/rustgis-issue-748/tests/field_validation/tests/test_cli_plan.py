"""CLI command-contract tests only. A passing test never implies RustGIS ran."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from sys import path

ROOT = Path(__file__).resolve().parents[1]
path.insert(0, str(ROOT))
from cli_plan import PlanFailure, audit_plan
from generate_fixtures import generate
from run_validation import run_engine


class TestCliContract(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.fixtures = self.root / "fixtures"
        self.out = self.root / "results"
        generate(self.fixtures)
        self.cases = run_engine(None, self.fixtures, self.out, plan_only=True)

    def test_all_sixteen_commands_are_planned_offline(self):
        result = audit_plan(self.cases, self.fixtures, self.out)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["case_count"], 16)
        self.assertFalse(result["executed"])
        self.assertEqual(self.cases["csv_xy_import"]["status"], "PLANNED")
        self.assertEqual(self.cases["topology_cases_gpkg_to_geojson"]["status"], "PLANNED")

    def test_csv_does_not_rely_on_column_auto_detection(self):
        cmd = self.cases["csv_xy_import"]["args"][2]
        name, data = cmd.split("=", 1)
        self.assertEqual(name, "layer.addData")
        self.assertEqual(json.loads(data)["x"], "longitude")
        self.assertEqual(json.loads(data)["y"], "latitude")
        self.assertEqual(json.loads(data)["crs"], "EPSG:4326")

    def test_changed_csv_axis_field_is_rejected(self):
        altered = copy.deepcopy(self.cases)
        cmd = altered["csv_xy_import"]["args"][2]
        name, data = cmd.split("=", 1)
        payload = json.loads(data)
        payload["x"] = "latitude"
        altered["csv_xy_import"]["args"][2] = name + "=" + json.dumps(payload)
        with self.assertRaisesRegex(PlanFailure, "CSV columns"):
            audit_plan(altered, self.fixtures, self.out)

    def test_no_network_or_output_escape(self):
        altered = copy.deepcopy(self.cases)
        altered["map_export"]["args"][2] = "https://example.org/upload.png"
        with self.assertRaises(PlanFailure):
            audit_plan(altered, self.fixtures, self.out)
        altered = copy.deepcopy(self.cases)
        altered["map_export"]["args"][2] = str(self.root.parent / "escape.png")
        with self.assertRaises(PlanFailure):
            audit_plan(altered, self.fixtures, self.out)

    def test_unknown_gp_tool_is_rejected(self):
        altered = copy.deepcopy(self.cases)
        value = altered["summarize_within"]["args"][6]
        name, data = value.split("=", 1)
        payload = json.loads(data)
        payload["tool"] = "unapprovedPlugin"
        altered["summarize_within"]["args"][6] = name + "=" + json.dumps(payload)
        with self.assertRaises(PlanFailure):
            audit_plan(altered, self.fixtures, self.out)

    def test_duplicate_output_destination_is_rejected(self):
        altered = copy.deepcopy(self.cases)
        b = altered["spatial_join"]["args"]
        cmd_index = len(b) - 1
        name, data = b[cmd_index].split("=", 1)
        payload = json.loads(data)
        payload["path"] = altered["spatial_join_within"]["expected_outputs"][0]
        b[cmd_index] = name + "=" + json.dumps(payload)
        altered["spatial_join"]["expected_outputs"][0] = payload["path"]
        with self.assertRaisesRegex(PlanFailure, "collides"):
            audit_plan(altered, self.fixtures, self.out)

    def test_plan_does_not_delete_or_overwrite_outputs(self):
        sentinel = self.out / "zone_counts.geojson"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("SENTINEL", encoding="ascii")
        _ = run_engine(None, self.fixtures, self.out, plan_only=True)
        self.assertEqual(sentinel.read_text(encoding="ascii"), "SENTINEL")

    def test_malformed_command_json_is_rejected(self):
        altered = copy.deepcopy(self.cases)
        altered["summarize_within"]["args"][6] = "gp.run={malformed"
        with self.assertRaisesRegex(PlanFailure, "bad CLI command JSON"):
            audit_plan(altered, self.fixtures, self.out)


if __name__ == "__main__":
    unittest.main()
