"""Mutation-resistant reference tests; never require a RustGIS executable."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from sys import path

ROOT = Path(__file__).resolve().parents[1]
path.insert(0, str(ROOT))
from generate_fixtures import generate, build
from reference_oracle import ReferenceFailure, by_id, length_km, reference_assertions
from run_validation import (
    CheckFailure, check_csv_xy, check_geodesic, check_gpkg, check_missing,
    check_projected_roundtrip, check_spatial_join, check_summarize,
    remove_stale_outputs, same_features,
)


class TestReference(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.dir = Path(self.work.name)
        generate(self.dir)

    def tearDown(self):
        self.work.cleanup()

    def write(self, filename, data):
        dest = self.dir / filename
        dest.write_text(json.dumps(data), encoding="utf-8")
        return dest

    def test_independent_oracle(self):
        result = reference_assertions(self.dir)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["zone_counts"], {"PLY-A": 3, "PLY-B": 2, "MCD-A": 3, "MCD-B": 2})
        self.assertEqual(result["projected_gpkg_checks"]["PLY"]["checked"], 4)
        self.assertEqual(result["topology_cases"]["PLY-HOLE"]["holes"], 1)
        self.assertEqual(result["topology_cases"]["MCD-MULTI"]["parts"], 2)

    def test_generation_is_reproducible_for_text_fixtures(self):
        originals = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in self.dir.iterdir() if p.suffix in (".geojson", ".csv")}
        generate(self.dir)
        regenerated = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in self.dir.iterdir() if p.suffix in (".geojson", ".csv")}
        self.assertEqual(originals, regenerated)
        self.assertIsNone(build()["missing_points.geojson"]["features"][0]["geometry"])

    def test_mixed_line_length(self):
        lines = build()["transects.geojson"]["features"]
        self.assertGreater(length_km(lines[1]["geometry"]), length_km(lines[0]["geometry"]))

    def test_roundtrip_allows_single_to_multi_promotion(self):
        base = build()["transects.geojson"]
        promoted = copy.deepcopy(base)
        geom = promoted["features"][0]["geometry"]
        self.assertEqual(geom["type"], "LineString")
        geom["coordinates"] = [geom["coordinates"]]
        geom["type"] = "MultiLineString"
        result = same_features(self.dir / "transects.geojson", self.write("promoted.geojson", promoted))
        self.assertEqual(result["features"], 3)

    def test_roundtrip_allows_polygon_promotion(self):
        base = build()["topology_cases.geojson"]
        promoted = copy.deepcopy(base)
        for feature in promoted["features"]:
            geom = feature["geometry"]
            if geom["type"] == "Polygon":
                geom["coordinates"] = [geom["coordinates"]]
                geom["type"] = "MultiPolygon"
        result = same_features(self.dir / "topology_cases.geojson", self.write("promoted_polys.geojson", promoted))
        self.assertEqual(result["features"], 3)

    def test_reject_displaced_geometry(self):
        modified = build()["zones.geojson"]
        modified["features"][0]["geometry"]["coordinates"][0][1][0] += 0.01
        with self.assertRaises(CheckFailure):
            same_features(self.dir / "zones.geojson", self.write("displaced.geojson", modified))

    def test_reject_dropped_hole(self):
        modified = build()["topology_cases.geojson"]
        modified["features"][0]["geometry"]["coordinates"] = modified["features"][0]["geometry"]["coordinates"][:1]
        with self.assertRaisesRegex(CheckFailure, "hole count"):
            same_features(self.dir / "topology_cases.geojson", self.write("hole_missing.geojson", modified))

    def test_reject_dropped_multipolygon_component(self):
        modified = build()["topology_cases.geojson"]
        modified["features"][1]["geometry"]["coordinates"] = modified["features"][1]["geometry"]["coordinates"][:1]
        with self.assertRaisesRegex(CheckFailure, "component"):
            same_features(self.dir / "topology_cases.geojson", self.write("part_missing.geojson", modified))

    def test_reject_attribute_change_even_when_geometry_matches(self):
        modified = build()["points.geojson"]
        modified["features"][3]["properties"]["score"] = None
        with self.assertRaisesRegex(CheckFailure, "score"):
            same_features(self.dir / "points.geojson", self.write("attr_modified.geojson", modified))

    def test_reject_attribute_type_change(self):
        modified = build()["points.geojson"]
        modified["features"][0]["properties"]["score"] = "3.0"
        with self.assertRaisesRegex(CheckFailure, "field type"):
            same_features(self.dir / "points.geojson", self.write("attr_type_changed.geojson", modified))

    def test_reject_duplicate_ids(self):
        modified = build()["points.geojson"]
        modified["features"].append(copy.deepcopy(modified["features"][0]))
        with self.assertRaisesRegex(ReferenceFailure, "duplicate"):
            by_id(modified)
        with self.assertRaisesRegex(ReferenceFailure, "duplicate"):
            same_features(self.dir / "points.geojson", self.write("duplicate.geojson", modified))

    def test_reject_missing_projected_fixture(self):
        (self.dir / "points_ply_26986.gpkg").unlink()
        with self.assertRaisesRegex(ReferenceFailure, "required projected GPKG missing"):
            reference_assertions(self.dir)

    def test_summarize_checker_rejects_wrong_count(self):
        summary = copy.deepcopy(build()["zones.geojson"])
        for feat in summary["features"]:
            feat["properties"]["point_count"] = {"PLY-A": 3, "PLY-B": 2, "MCD-A": 3, "MCD-B": 2}[feat["properties"]["id"]]
        output = self.write("summary.geojson", summary)
        self.assertEqual(check_summarize(output)["PLY-A"], 3)
        summary["features"][0]["properties"]["point_count"] += 1
        with self.assertRaises(CheckFailure):
            check_summarize(self.write("summary_mutated.geojson", summary))

    def joined_fixture(self, expected_key):
        point_fc = build()["points.geojson"]
        lookup = {p["properties"]["id"]: p for p in point_fc["features"]}
        exp = json.loads((ROOT / "expected" / "reference_snapshot.json").read_text())[expected_key]
        result = []
        for ident, zones in exp.items():
            for zone in (zones or [None]):
                row = copy.deepcopy(lookup[ident])
                row["properties"].update({"join_count": len(zones), "zone_id": zone,
                                          "zone_zone_id": zone, "zone_source_class": "synthetic" if zone is not None else None,
                                          "zone_authority": "none" if zone is not None else None,
                                          "zone_site": ident.split("-")[0] if zone is not None else None})
                result.append(row)
        return {"type": "FeatureCollection", "features": result}

    def test_join_comparator_accepts_expected_intersects_and_within(self):
        self.assertEqual(check_spatial_join(self.write("intersects.geojson", self.joined_fixture("joins_intersects")))["rows"], 12)
        self.assertEqual(check_spatial_join(self.write("within.geojson", self.joined_fixture("joins_within")),
                                            "joins_within")["rows"], 10)

    def test_join_comparator_rejects_fake_unmatched_duplicate(self):
        joined = self.joined_fixture("joins_intersects")
        joined["features"].append(copy.deepcopy(joined["features"][0]))
        with self.assertRaises(CheckFailure):
            check_spatial_join(self.write("duplicate_join.geojson", joined))

    def test_join_comparator_rejects_cross_region_metadata(self):
        joined = self.joined_fixture("joins_intersects")
        for row in joined["features"]:
            if row["properties"]["zone_zone_id"] is not None:
                row["properties"]["zone_site"] = "OTHER"
                break
        with self.assertRaisesRegex(CheckFailure, "cross-region"):
            check_spatial_join(self.write("bad_join.geojson", joined))

    def test_null_geometry_retained_is_pass(self):
        src = self.dir / "missing_points.geojson"
        result = check_missing(src, src)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["retained_null_geometry"])

    def test_missing_geometry_dropped_silently_is_blocked(self):
        src = self.dir / "missing_points.geojson"
        output = build()["missing_points.geojson"]
        output["features"] = output["features"][1:]
        dest = self.write("silent_drop.geojson", output)
        result = check_missing(dest, src, stdout_text='{"leftOut":0}\n')
        self.assertEqual(result["status"], "BLOCKED")

    def test_missing_geometry_explicitly_dropped_is_pass_with_notice(self):
        src = self.dir / "missing_points.geojson"
        output = build()["missing_points.geojson"]
        output["features"] = output["features"][1:]
        dest = self.write("explicit_drop.geojson", output)
        result = check_missing(dest, src, stdout_text='{"leftOut":1}\n')
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["omission_explicitly_disclosed"])

    def test_missing_geometry_control_displacement_fails(self):
        src = self.dir / "missing_points.geojson"
        output = build()["missing_points.geojson"]
        output["features"][1]["geometry"]["coordinates"][0] += 0.01
        with self.assertRaises(CheckFailure):
            check_missing(self.write("null_control_moved.geojson", output), src)

    def test_projected_checker_rejects_displacement(self):
        point_fc = build()["points.geojson"]
        originals = by_id(point_fc)
        selected = [p for p in point_fc["features"] if p["properties"]["site"] == "PLY" and "EDGE" not in p["properties"]["id"]]
        output = self.write("projected_pass.geojson", {"type": "FeatureCollection", "features": selected})
        self.assertEqual(check_projected_roundtrip(output, originals, [p["properties"]["id"] for p in selected])["count"], 4)
        altered = copy.deepcopy(selected)
        altered[0]["geometry"]["coordinates"][0] += 0.001
        with self.assertRaises(CheckFailure):
            check_projected_roundtrip(self.write("projected_fail.geojson", {"type": "FeatureCollection", "features": altered}),
                                      originals, [p["properties"]["id"] for p in selected])

    def test_spatial_join_validates_target_and_join_source_integrity(self):
        original = self.dir / "points.geojson"
        joins = self.dir / "zones.geojson"
        baseline = self.joined_fixture("joins_intersects")
        path = self.write("original_join.geojson", baseline)
        self.assertEqual(check_spatial_join(path, "joins_intersects", original, joins)["rows"], 12)

        displaced = copy.deepcopy(baseline)
        displaced["features"][0]["geometry"]["coordinates"][0] += .001
        with self.assertRaisesRegex(CheckFailure, "geometry moved"):
            check_spatial_join(self.write("displaced_join.geojson", displaced),
                               "joins_intersects", original, joins)

        wrong_source = copy.deepcopy(baseline)
        wrong_source["features"][0]["properties"]["zone_source_class"] = "unsourced"
        with self.assertRaisesRegex(CheckFailure, "joined field"):
            check_spatial_join(self.write("tampered_join.geojson", wrong_source),
                               "joins_intersects", original, joins)

    def test_spatial_join_rejects_modified_target_attribute(self):
        altered = self.joined_fixture("joins_within")
        altered["features"][0]["properties"]["score"] = 999
        with self.assertRaisesRegex(CheckFailure, "target field"):
            check_spatial_join(self.write("join_target_changed.geojson", altered),
                               "joins_within", self.dir / "points.geojson", self.dir / "zones.geojson")

    def test_summarize_checks_geometry_and_attributes_not_only_counts(self):
        summary = copy.deepcopy(build()["zones.geojson"])
        for feature in summary["features"]:
            feature["properties"]["point_count"] = {"PLY-A": 3, "PLY-B": 2, "MCD-A": 3, "MCD-B": 2}[feature["properties"]["id"]]
        self.assertEqual(check_summarize(self.write("summary_valid.geojson", summary),
                                         self.dir / "zones.geojson")["PLY-B"], 2)
        summary["features"][1]["geometry"]["coordinates"][0][1][0] += .01
        with self.assertRaises(CheckFailure):
            check_summarize(self.write("summary_displaced.geojson", summary), self.dir / "zones.geojson")

    def test_csv_checker_preserves_null_zero_and_attributes(self):
        points = build()["points.geojson"]
        originals = by_id(points)
        self.assertEqual(check_csv_xy(self.dir / "points.geojson", originals)["count"], 10)
        changed = copy.deepcopy(points)
        changed["features"][3]["properties"]["score"] = None  # zero != missing
        with self.assertRaisesRegex(CheckFailure, "CSV field score"):
            check_csv_xy(self.write("csv_zero_lost.geojson", changed), originals)

    def test_geodesic_length_checker_does_not_ignore_geometry_corruption(self):
        lines = copy.deepcopy(build()["transects.geojson"])
        frozen = json.loads((ROOT / "expected" / "reference_snapshot.json").read_text())
        for feature in lines["features"]:
            feature["properties"]["length_km"] = frozen["reference_spherical_lengths_km"][feature["properties"]["id"]]
        src = self.dir / "transects.geojson"
        self.assertEqual(len(check_geodesic(self.write("length_valid.geojson", lines), src)), 3)
        lines["features"][0]["geometry"]["coordinates"][1][0] += .001
        with self.assertRaises(CheckFailure):
            check_geodesic(self.write("length_geometry_bad.geojson", lines), src)

    def test_gpkg_is_verified_before_reimport(self):
        import fiona
        source = self.dir / "zones.geojson"
        result = self.dir / "test_export.gpkg"
        props = {"id": "str", "site": "str", "zone_id": "str", "source_class": "str", "authority": "str"}
        with fiona.open(result, "w", driver="GPKG", layer="synthetic_zones",
                        schema={"geometry": "Polygon", "properties": props}, crs="EPSG:4326") as dst:
            for feature in build()["zones.geojson"]["features"]:
                dst.write(feature)
        self.assertEqual(check_gpkg(result, source)["features"], 4)
        bad_crs = self.dir / "wrong_crs.gpkg"
        with fiona.open(bad_crs, "w", driver="GPKG", layer="synthetic_zones",
                        schema={"geometry": "Polygon", "properties": props}, crs="EPSG:3857") as dst:
            for feature in build()["zones.geojson"]["features"]:
                dst.write(feature)
        with self.assertRaisesRegex(CheckFailure, "wrong CRS"):
            check_gpkg(bad_crs, source)

    def test_projected_checker_detects_attribute_mutation(self):
        originals = by_id(build()["points.geojson"])
        selected = [x for x in build()["points.geojson"]["features"]
                    if x["properties"]["site"] == "MCD" and "EDGE" not in x["properties"]["id"]]
        selected[0]["properties"]["status"] = "not-the-original-status"
        with self.assertRaisesRegex(CheckFailure, "projected status"):
            check_projected_roundtrip(self.write("wrong_status.geojson", {
                "type": "FeatureCollection", "features": selected}), originals,
                [x["properties"]["id"] for x in selected])

    def test_stale_output_cleanup(self):
        stale = self.dir / "old.geojson"
        stale.write_text("stale", encoding="utf-8")
        remove_stale_outputs([stale])
        self.assertFalse(stale.exists())


if __name__ == "__main__":
    unittest.main()
