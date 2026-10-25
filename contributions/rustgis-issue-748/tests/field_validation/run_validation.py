#!/usr/bin/env python3
"""Synthetic RustGIS CLI validation against independent geospatial oracles.

This tool only reads synthetic inputs, writes a local results directory and runs
specified local executables. It never commits, pushes, posts or opens a PR.
Missing engine execution is always SKIPPED; an inconclusive case is BLOCKED.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from generate_fixtures import generate
from cli_plan import audit_plan
from reference_oracle import (
    by_id, count_interior_rings, count_polygon_parts, length_km, load,
    reference_assertions,
)

HERE = Path(__file__).resolve().parent
EXPECTED = load(HERE / "expected" / "reference_snapshot.json")


class CheckFailure(AssertionError):
    """A strict engine-oracle comparison was violated."""


def ensure(value, message):
    if not value:
        raise CheckFailure(message)


def read_collection(path):
    data = load(path)
    ensure(data.get("type") == "FeatureCollection", f"not GeoJSON: {path}")
    ensure(isinstance(data.get("features"), list), f"invalid feature list: {path}")
    return data


def _component_count(geometry):
    if geometry.geom_type.startswith("Multi"):
        return len(geometry.geoms)
    return 1


def _same_geometry(a, b, ident, tolerance):
    """Allow single->multi wrapping but not a dropped hole or polygon part.

    Hausdorff distance alone is unsafe: deleting an interior ring leaves the
    external boundary in place and may report zero distance for some shapes.
    """
    ensure(a.is_valid and b.is_valid and not a.is_empty and not b.is_empty,
           f"invalid or empty geometry for {ident}")
    ensure(a.geom_type.replace("Multi", "") == b.geom_type.replace("Multi", ""),
           f"geometry family changed for {ident}: {a.geom_type} -> {b.geom_type}")
    ensure(_component_count(a) == _component_count(b),
           f"geometry component lost/split for {ident}: {_component_count(a)} -> {_component_count(b)}")
    if a.geom_type.endswith("Polygon"):
        ensure(count_interior_rings(a) == count_interior_rings(b),
               f"hole count changed for {ident}")
    hausdorff = a.hausdorff_distance(b)
    ensure(math.isfinite(hausdorff) and hausdorff <= tolerance,
           f"geometry moved for {ident}: {hausdorff} degrees")
    if a.geom_type.endswith("Polygon"):
        area_delta = a.symmetric_difference(b).area
        area_budget = tolerance * (a.length + b.length) / 2 + tolerance ** 2
        ensure(math.isfinite(area_delta) and area_delta <= area_budget,
               f"polygon topology changed for {ident}: symmetric difference={area_delta} square degrees")
    elif a.geom_type.endswith("LineString"):
        ensure(abs(a.length - b.length) <= tolerance * 8,
               f"line length/topology changed for {ident}")


def same_features(original, exported, position_tolerance=1e-6):
    from shapely.geometry import shape
    source_fc = read_collection(original)
    final_fc = read_collection(exported)
    before, after = by_id(source_fc), by_id(final_fc)
    ensure(set(before) == set(after), f"ID loss/change: before={sorted(before)}, after={sorted(after)}")
    for ident, source in before.items():
        final = after[ident]
        g0, g1 = source["geometry"], final["geometry"]
        ensure((g0 is None) == (g1 is None), f"geometry nullness changed for {ident}")
        if g0 is not None:
            _same_geometry(shape(g0), shape(g1), ident, position_tolerance)
        for field, value in source["properties"].items():
            ensure(field in final["properties"], f"lost field {field} in {ident}")
            actual = final["properties"][field]
            ensure(type(value) is type(actual) or (isinstance(value, float) and isinstance(actual, (float, int))
                  and not isinstance(actual, bool)),
                  f"field type changed for {ident}.{field}: {type(value).__name__}->{type(actual).__name__}")
            ensure(value == actual, f"changed {field} on {ident}: {value!r} vs {actual!r}")
    return {"features": len(before), "tolerance_degrees": position_tolerance,
            "geometry_holes_verified": True, "component_counts_verified": True}


def check_summarize(path, source=None):
    if source is not None:
        same_features(source, path, EXPECTED["roundtrip_tolerance_degrees"])
    got = {ident: f["properties"].get("point_count")
           for ident, f in by_id(read_collection(path)).items()}
    ensure(got == EXPECTED["zone_intersect_counts"], f"summary mismatch: {got}")
    return got


def check_spatial_join(path, expected_key="joins_intersects", original=None, join_source=None):
    from shapely.geometry import shape
    targets = by_id(read_collection(original)) if original is not None else None
    joins = by_id(read_collection(join_source)) if join_source is not None else None
    rows = read_collection(path)["features"]
    expected = EXPECTED[expected_key]
    grouped = collections.defaultdict(list)
    row_counter = collections.Counter()
    for row in rows:
        props = row["properties"]
        ident = props["id"]
        ensure(ident in expected, f"unknown joined target {ident}")
        ensure(type(props.get("join_count")) is int, f"{ident}: join_count must be an integer")
        if targets is not None:
            baseline = targets[ident]
            for field, value in baseline["properties"].items():
                ensure(field in props and props[field] == value,
                       f"{ident}: target field {field} lost or modified")
            ensure(row.get("geometry") is not None, f"{ident}: target point geometry missing")
            _same_geometry(shape(baseline["geometry"]), shape(row["geometry"]), ident,
                           EXPECTED["roundtrip_tolerance_degrees"])
        row_counter[ident] += 1
        want = expected[ident]
        ensure(props.get("join_count") == len(want),
               f"join_count incorrect for {ident}: {props.get('join_count')} != {len(want)}")
        zone = props.get("zone_zone_id")
        if zone is not None:
            grouped[ident].append(zone)
            ensure(props.get("zone_authority") == "none", f"join metadata altered for {ident}")
            ensure(props.get("zone_site") == props.get("site"), f"cross-region join for {ident}")
            if joins is not None:
                ensure(zone in joins, f"{ident}: joined zone {zone} not found in source")
                for field, value in joins[zone]["properties"].items():
                    key = f"zone_{field}"
                    ensure(key in props and props[key] == value,
                           f"{ident}: joined field {key} lost or modified")
        else:
            ensure(not want, f"join match unexpectedly null for {ident}")
            ensure(props.get("zone_authority") is None, f"unmatched row has joined metadata: {ident}")
            if joins is not None:
                for field in next(iter(joins.values()))["properties"]:
                    key = f"zone_{field}"
                    ensure(key in props and props[key] is None,
                           f"{ident}: unmatched row has non-null/missing {key}")
            grouped[ident] = grouped[ident]
    ensure(set(row_counter) == set(expected), f"missing joined target rows: {set(expected) - set(row_counter)}")
    for ident, matches in expected.items():
        ensure(row_counter[ident] == max(1, len(matches)),
               f"wrong multiplicity for {ident}: {row_counter[ident]}")
    observed = {ident: sorted(grouped[ident]) for ident in expected}
    ensure(observed == expected, f"join mismatch: {observed}")
    return {"rows": len(rows), "matches": observed, "relationship": expected_key}


def check_geodesic(path, original):
    same_features(original, path, EXPECTED["roundtrip_tolerance_degrees"])
    observed = by_id(read_collection(path))
    expected = by_id(read_collection(original))
    ensure(set(observed) == set(expected), "transect IDs changed")
    lengths = {}
    for ident, feat in observed.items():
        expected_km = EXPECTED["reference_spherical_lengths_km"][ident]
        ensure(abs(length_km(expected[ident]["geometry"]) - expected_km) < 1e-8,
               f"fixture length changed for {ident}")
        actual = feat["properties"].get("length_km")
        ensure(isinstance(actual, (float, int)) and not isinstance(actual, bool),
               f"no numeric length_km for {ident}: {actual}")
        ensure(math.isfinite(actual) and abs(actual - expected_km) <= EXPECTED["length_tolerance_km"],
               f"geodesic length {ident}: engine={actual:.8f}, spherical_ref={expected_km:.8f} km")
        lengths[ident] = {"rustgis_km": actual, "reference_km": expected_km}
    return lengths


def check_csv_xy(path, originals):
    """CSV point coordinates and meaningful fields must survive explicit XY ingestion."""
    from pyproj import Geod
    rows = by_id(read_collection(path))
    ensure(set(rows) == set(originals), f"CSV import lost/added IDs: {set(rows) ^ set(originals)}")
    geod = Geod(ellps="WGS84")
    errors = {}
    for ident, feat in rows.items():
        geo = feat["geometry"]
        ensure(geo is not None and geo.get("type") == "Point", f"CSV import wrong geometry: {ident}")
        actual = geo["coordinates"]
        expected = originals[ident]["geometry"]["coordinates"]
        delta = abs(geod.inv(*actual, *expected)[2])
        ensure(math.isfinite(delta) and delta < 0.5, f"CSV coordinate error {ident}: {delta:.3f} m")
        for field, want in originals[ident]["properties"].items():
            ensure(field in feat["properties"] and feat["properties"][field] == want,
                   f"CSV field {field} changed or lost on {ident}")
        errors[ident] = round(delta, 6)
    return {"count": len(rows), "max_error_m": max(errors.values()),
            "explicit_columns_checked": ["longitude", "latitude"]}


def check_selection(path, original=None):
    from shapely.geometry import shape
    observed = by_id(read_collection(path))
    wanted = EXPECTED["expected_null_attribute_ids"]
    ensure(set(observed) == set(wanted), f"null filter mismatch: {list(observed)} vs {wanted}")
    for ident in observed:
        ensure(observed[ident]["properties"].get("score") is None,
               f"null filter returned non-null score: {ident}")
        if original is not None:
            source = by_id(read_collection(original))[ident]
            for field, want in source["properties"].items():
                ensure(field in observed[ident]["properties"] and observed[ident]["properties"][field] == want,
                       f"selected feature {ident} lost/modified {field}")
            _same_geometry(shape(source["geometry"]), shape(observed[ident]["geometry"]),
                           ident, EXPECTED["roundtrip_tolerance_degrees"])
    return sorted(observed)


def check_projected_roundtrip(path, originals, expected_ids):
    from pyproj import Geod
    from shapely.geometry import shape
    geod = Geod(ellps="WGS84")
    rows = by_id(read_collection(path))
    ensure(set(rows) == set(expected_ids), f"projected roundtrip IDs: {set(rows)} != {set(expected_ids)}")
    errors = {}
    for ident, feat in rows.items():
        source = originals[ident]
        lon0, lat0 = shape(source["geometry"]).coords[0]
        lon1, lat1 = shape(feat["geometry"]).coords[0]
        delta = abs(geod.inv(lon0, lat0, lon1, lat1)[2])
        ensure(math.isfinite(delta) and delta <= EXPECTED["projected_roundtrip_tolerance_m"],
               f"{ident}: {delta:.3f} m exceeds tolerance")
        for field in ("id", "site", "status", "score"):
            want = source["properties"][field]
            have = feat["properties"].get(field)
            ensure(field in feat["properties"] and have == want,
                   f"{ident}: projected {field} attribute was changed or lost")
        errors[ident] = round(delta, 6)
    return {"count": len(rows), "ellipsoidal_error_m": errors}


def check_missing(path, original, stdout_text="", stderr_text=""):
    """Missing geometry is PASS only if retained or omission was disclosed."""
    from pyproj import Geod
    rows = by_id(read_collection(path))
    originals = by_id(read_collection(original))
    ensure(set(rows) in ({"NULL-02"}, {"NULL-01", "NULL-02"}),
           f"unexpected or missing feature IDs: {sorted(rows)}")
    control = rows["NULL-02"]
    ensure(control["geometry"] is not None and control["geometry"].get("type") == "Point",
           "valid control point was lost/changed to null")
    a = control["geometry"]["coordinates"]
    b = originals["NULL-02"]["geometry"]["coordinates"]
    error_m = abs(Geod(ellps="WGS84").inv(*a, *b)[2])
    ensure(error_m <= 0.5, f"valid control point displaced {error_m:.3f} m")
    for field, want in originals["NULL-02"]["properties"].items():
        ensure(field in control["properties"] and control["properties"][field] == want,
               f"control field {field} changed or lost")
    if "NULL-01" in rows:
        ensure(rows["NULL-01"]["geometry"] is None, "fabricated geometry for missing coordinate")
        for field, want in originals["NULL-01"]["properties"].items():
            ensure(field in rows["NULL-01"]["properties"] and rows["NULL-01"]["properties"][field] == want,
                   f"missing-geometry feature field {field} changed or lost")
        return {"status": "PASS", "retained_null_geometry": True,
                "valid_point_error_m": round(error_m, 6)}

    # The writer publishes a JSON command result with `leftOut` when its
    # exporter explicitly leaves out non-drawable features. If the importer
    # silently dropped the feature upstream, its export typically says zero.
    disclosed = False
    for line in stdout_text.splitlines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get("leftOut") == 1:
            disclosed = True
    if not disclosed:
        disclosed = bool(re.search(r"\b1\s+feature\b.*\bleft out\b", stderr_text, re.I))
    if disclosed:
        return {"status": "PASS", "retained_null_geometry": False,
                "omission_explicitly_disclosed": True, "valid_point_error_m": round(error_m, 6)}
    return {"status": "BLOCKED", "retained_null_geometry": False,
            "reason": "null feature omitted without an observed count/notice; review import and export logs",
            "valid_point_error_m": round(error_m, 6)}


def check_gpkg(path, source):
    """Read a newly written GeoPackage independently, before RustGIS reimports it."""
    import fiona
    from shapely.geometry import shape
    source_rows = by_id(read_collection(source))
    with fiona.open(path, "r") as dataset:
        ensure(dataset.driver == "GPKG", "output did not open as a GeoPackage")
        ensure(dataset.crs is not None and dataset.crs.to_epsg() == 4326,
               f"roundtrip GeoPackage has wrong CRS: {dataset.crs}")
        observed = {}
        for row in dataset:
            props = dict(row["properties"])
            ident = props.get("id")
            ensure(isinstance(ident, str) and ident not in observed,
                   f"duplicate/missing GeoPackage ID: {ident}")
            ensure(ident in source_rows, f"unexpected GeoPackage ID: {ident}")
            source_feature = source_rows[ident]
            for field, want in source_feature["properties"].items():
                ensure(field in props and props[field] == want,
                       f"{ident}: GeoPackage attribute {field} changed or lost")
            original_geometry = source_feature["geometry"]
            ensure(original_geometry is not None and row["geometry"] is not None,
                   f"{ident}: geometry missing in GeoPackage")
            _same_geometry(shape(original_geometry), shape(row["geometry"]), ident,
                           EXPECTED["roundtrip_tolerance_degrees"])
            observed[ident] = True
    ensure(set(observed) == set(source_rows), f"GeoPackage missing IDs: {set(source_rows)-set(observed)}")
    return {"features": len(observed), "crs": "EPSG:4326", "independent_reader": "Fiona",
            "topology_checked": True}


def check_png(path, width=640, height=480):
    from PIL import Image
    with Image.open(path) as img:
        img.load()
        ensure(img.format == "PNG", "map export is not PNG")
        ensure(img.size == (width, height), f"wrong dimensions: {img.size}")
        rgb = img.convert("RGB")
        pix = list(rgb.getdata())
        diversity = len(set(pix[::max(1, len(pix) // 10000)]))
        ensure(diversity >= 2, f"map appears flat: {diversity} sampled colours")
    return {"format": "PNG", "size": [width, height],
            "sampled_colours": diversity, "bytes": path.stat().st_size}


def command(name, executable, args, logs_dir, timeout_s=240):
    logs_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(executable), *[str(a) for a in args]]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CheckFailure(f"{name}: rustgis-cli timed out after {timeout_s}s") from exc
    stdout = logs_dir / f"{name}.stdout.log"
    stderr = logs_dir / f"{name}.stderr.log"
    stdout.write_text(run.stdout, encoding="utf-8")
    stderr.write_text(run.stderr, encoding="utf-8")
    ensure(run.returncode == 0, f"{name}: exit={run.returncode}; see logs for stderr")
    # Relative paths are portable when the results directory is moved/shared.
    return {"exit": run.returncode, "argument_count": len(args),
            "stdout_log": f"logs/{stdout.name}", "stderr_log": f"logs/{stderr.name}"}


def c(identifier, obj):
    return f"{identifier}={json.dumps(obj, separators=(',', ':'), sort_keys=True)}"


def remove_stale_outputs(paths):
    for path in paths:
        path = Path(path)
        if path.exists():
            ensure(path.is_file(), f"expected a regular output file, got: {path}")
            path.unlink()


def run_engine(cli, fixture_dir: Path, out: Path, plan_only=False):
    tests = {}
    out.mkdir(parents=True, exist_ok=True)
    logs = out / "logs"
    zones = fixture_dir / "zones.geojson"
    points = fixture_dir / "points.geojson"
    lines = fixture_dir / "transects.geojson"
    topology = fixture_dir / "topology_cases.geojson"
    missing = fixture_dir / "missing_points.geojson"
    originals = by_id(read_collection(points))

    def run_check(name, args, checker, output_files):
        if plan_only:
            tests[name] = {"status": "PLANNED", "args": [str(a) for a in args],
                           "expected_outputs": [str(p) for p in output_files]}
            return
        try:
            remove_stale_outputs(output_files)
            cmd_report = command(name, cli, args, logs)
            for result_path in output_files:
                ensure(Path(result_path).is_file() and Path(result_path).stat().st_size > 0,
                       f"{name}: no new output: {Path(result_path).name}")
            details = checker()
            outcome = details.get("status", "PASS") if isinstance(details, dict) else "PASS"
            ensure(outcome in {"PASS", "BLOCKED"}, f"invalid checker outcome: {outcome}")
            tests[name] = {"status": outcome, "details": details, "invocation": cmd_report}
        except Exception as exc:
            tests[name] = {"status": "FAIL", "message": f"{type(exc).__name__}: {exc}"}

    count_out = out / "zone_counts.geojson"
    run_check("summarize_within", ["run", "--data", zones, "--data", points,
        "--cmd", c("gp.run", {"tool": "countPoints", "params": {
            "polygons": "zones", "points": "points", "output": "counts"}}),
        "--cmd", c("share.exportLayer", {"layer": "counts", "path": str(count_out)})],
        lambda: check_summarize(count_out, zones), [count_out])

    for relationship, key, output_name in [
        ("Intersects", "joins_intersects", "spatial_join"),
        ("Within", "joins_within", "spatial_join_within"),
    ]:
        output = out / f"{output_name}.geojson"
        run_check(output_name, ["run", "--data", points, "--data", zones,
            "--cmd", c("gp.run", {"tool": "spatialJoin", "params": {
                "target": "points", "join": "zones", "match": relationship,
                "operation": "Join one to many", "prefix": "zone_",
                "keepAll": "Keep all", "output": "point_zone_join"}}),
            "--cmd", c("share.exportLayer", {"layer": "point_zone_join", "path": str(output)})],
            lambda output=output, key=key: check_spatial_join(output, key, points, zones), [output])

    lengths_out = out / "transect_lengths.geojson"
    run_check("geodesic_lengths", ["run", "--data", lines,
        "--cmd", c("gp.run", {"tool": "calculateGeometry", "params": {"input": "transects"}}),
        "--cmd", c("share.exportLayer", {"layer": "transects", "path": str(lengths_out)})],
        lambda: check_geodesic(lengths_out, lines), [lengths_out])

    csv_out = out / "csv_points.geojson"
    run_check("csv_xy_import", ["run",
        "--cmd", c("layer.addData", {"path": str(fixture_dir / "points.csv"),
                                      "name": "csv_points", "x": "longitude",
                                      "y": "latitude", "crs": "EPSG:4326"}),
        "--cmd", c("share.exportLayer", {"layer": "csv_points", "path": str(csv_out)})],
        lambda: check_csv_xy(csv_out, originals), [csv_out])

    selected = out / "missing_score_selection.geojson"
    run_check("null_attribute_filter", ["run", "--data", points,
        "--cmd", c("select.byAttributes", {"layer": "points", "where": "score IS NULL"}),
        "--cmd", c("select.layerFromSelection", {"layer": "points"}),
        "--cmd", c("share.exportLayer", {"path": str(selected)})],
        lambda: check_selection(selected, points), [selected])

    # GeoPackage writing and reading take place in separate RustGIS commands.
    for case, src in [("zones", zones), ("transects", lines), ("topology_cases", topology)]:
        gpkg = out / f"{case}_roundtrip.gpkg"
        exported = out / f"{case}_roundtrip.geojson"
        first = f"{case}_geojson_to_gpkg"
        second = f"{case}_gpkg_to_geojson"
        run_check(first, ["run", "--data", src,
            "--cmd", c("share.exportLayer", {"path": str(gpkg), "crs": "EPSG:4326"})],
            lambda gpkg=gpkg, src=src: check_gpkg(gpkg, src), [gpkg])
        if tests[first]["status"] in {"PASS", "PLANNED"}:
            run_check(second, ["run", "--data", gpkg,
                "--cmd", c("share.exportLayer", {"path": str(exported)})],
                lambda src=src, exported=exported: same_features(
                    src, exported, EXPECTED["roundtrip_tolerance_degrees"]), [exported])
        else:
            tests[second] = {"status": "BLOCKED", "reason": f"prerequisite {first} failed"}

    for site, epsg in EXPECTED["projected_crs"].items():
        native = fixture_dir / f"points_{site.lower()}_{epsg.split(':')[-1]}.gpkg"
        output = out / f"points_{site.lower()}_to_wgs84.geojson"
        wanted = [ident for ident, feat in originals.items()
                  if feat["properties"]["site"] == site and "EDGE" not in ident]
        run_check(f"projected_{site.lower()}", ["run", "--data", native,
            "--cmd", c("share.exportLayer", {"path": str(output), "crs": "EPSG:4326"})],
            lambda output=output, wanted=wanted: check_projected_roundtrip(output, originals, wanted),
            [output])

    missing_output = out / "missing_points_roundtrip.geojson"
    run_check("missing_geometry", ["run", "--data", missing,
        "--cmd", c("share.exportLayer", {"path": str(missing_output)})],
        lambda: check_missing(missing_output, missing,
            stdout_text=(logs / "missing_geometry.stdout.log").read_text(encoding="utf-8"),
            stderr_text=(logs / "missing_geometry.stderr.log").read_text(encoding="utf-8")),
        [missing_output])

    png = out / "zones_map.png"
    run_check("map_export", ["render", zones, png, "--width", "640", "--height", "480"],
              lambda: check_png(png), [png])
    return tests


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=HERE / "results")
    ap.add_argument("--cli", type=str, default=None,
                    help="path to rustgis-cli; automatically detected by default")
    ap.add_argument("--require-cli", action="store_true", help="fail closed when RustGIS is unavailable")
    ap.add_argument("--offline", action="store_true", help="only independent reference tests")
    ap.add_argument("--plan-only", action="store_true",
                    help="validate CLI commands offline; do not launch RustGIS or modify engine outputs")
    args = ap.parse_args()
    if args.plan_only and args.require_cli:
        ap.error("--plan-only cannot be combined with --require-cli")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    fixtures = out / "fixtures"
    report = {
        "suite": "rustgis-validation", "version": EXPECTED["fixture_version"],
        "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "fixture_classification": "entirely synthetic",
        "host": {"python": sys.version.split()[0], "platform": platform.platform()},
        "upstream_issue": "https://github.com/opengeos/RustGIS/issues/748",
        "reviewed_cli_contract": load(HERE / "expected" / "upstream_cli_contract.json"),
        "changes_published": False, "engine_status": "SKIPPED", "engine_checks": {},
    }
    try:
        generate(fixtures)
        report["reference"] = reference_assertions(fixtures)
    except Exception as exc:
        report["reference"] = {"status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"}

    if args.plan_only and report["reference"]["status"] == "PASS":
        try:
            planned = run_engine(None, fixtures, out / "engine", plan_only=True)
            report["engine_plan"] = audit_plan(planned, fixtures, out / "engine")
            report["engine_plan"]["argv"] = {name: case["args"] for name, case in sorted(planned.items())}
        except Exception as exc:
            report["engine_plan"] = {"status": "FAIL", "reason": f"{type(exc).__name__}: {exc}"}
    cli = None if args.offline or args.plan_only else (args.cli or shutil.which("rustgis-cli"))
    if cli and report["reference"]["status"] == "PASS":
        try:
            planned = run_engine(None, fixtures, out / "engine", plan_only=True)
            report["engine_plan"] = audit_plan(planned, fixtures, out / "engine")
            report["engine_plan"]["argv"] = {name: case["args"] for name, case in sorted(planned.items())}
            tests = run_engine(cli, fixtures, out / "engine")
            states = {test["status"] for test in tests.values()}
            report["engine_status"] = ("FAIL" if "FAIL" in states
                                       else "INCOMPLETE" if "BLOCKED" in states
                                       else "PASS")
            report["engine_checks"] = tests
            try:
                version = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=15)
                if version.returncode == 0:
                    report["engine_version"] = (version.stdout or version.stderr).strip() or None
                else:
                    report["engine_version"] = None
                    report["engine_version_note"] = "No supported --version command; identify binary using pinned release SHA256 provenance."
            except Exception:
                report["engine_version"] = None
                report["engine_version_note"] = "Could not query --version; refer to pinned release SHA256 provenance."
        except Exception as exc:
            report["engine_status"] = "FAIL"
            report["engine_error"] = f"{type(exc).__name__}: {exc}"

    report["completed_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"Reference: {report['reference']['status']}; RustGIS engine: {report['engine_status']}")
    print(f"Report: {out / 'validation_report.json'}")
    if report["reference"]["status"] != "PASS" or report["engine_status"] == "FAIL" \
       or report.get("engine_plan", {}).get("status") == "FAIL":
        return 1
    if report["engine_status"] == "INCOMPLETE":
        return 2
    if args.require_cli and report["engine_status"] == "SKIPPED":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
