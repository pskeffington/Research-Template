#!/usr/bin/env python3
"""Offline audit of the *planned* RustGIS CLI invocations; no engine execution.

The allowlist reflects the RustGIS source contract reviewed on 2026-10-25.
A PASS from this module validates argument shapes, local paths, and declared
outputs. It is NEVER evidence that rustgis-cli executed successfully.
"""
from __future__ import annotations

import json
from pathlib import Path


class PlanFailure(ValueError):
    """A generated CLI command disagrees with the reviewed local-only contract."""


def require(value, message):
    if not value:
        raise PlanFailure(message)


def local_path(value, roots, label):
    require(isinstance(value, str) and bool(value), f"{label}: expected a path string")
    require(not value.startswith(("http:", "https:", "s3:", "file:")), f"{label}: network or URI path forbidden")
    dest = Path(value).resolve()
    require(any(dest.is_relative_to(root.resolve()) for root in roots),
            f"{label}: path escapes the synthetic fixture/results workspace: {dest}")
    return dest


TOOL_PARAMS = {
    "countPoints": {"polygons", "points", "output"},
    "spatialJoin": {"target", "join", "match", "operation", "keepAll", "prefix", "output"},
    "calculateGeometry": {"input"},
}
ALLOWED_COMMANDS = {"gp.run", "share.exportLayer", "select.byAttributes", "select.layerFromSelection", "layer.addData"}
EXPECTED_CASES = {
    "summarize_within", "spatial_join", "spatial_join_within", "geodesic_lengths",
    "csv_xy_import", "null_attribute_filter", "zones_geojson_to_gpkg",
    "zones_gpkg_to_geojson", "transects_geojson_to_gpkg", "transects_gpkg_to_geojson",
    "topology_cases_geojson_to_gpkg", "topology_cases_gpkg_to_geojson",
    "projected_ply", "projected_mcd", "missing_geometry", "map_export",
}


def audit_plan(cases: dict, fixtures: Path, out: Path):
    """Audit 16 synthetic test commands against an intentionally narrow contract.

    No subprocess is launched and no source/output artifact is modified.
    """
    fixtures, out = Path(fixtures).resolve(), Path(out).resolve()
    require(set(cases) == EXPECTED_CASES,
            f"test case inventory drift: missing={sorted(EXPECTED_CASES - set(cases))}; "
            f"unexpected={sorted(set(cases) - EXPECTED_CASES)}")
    seen_exports = set()
    reviewed = {}
    for case, entry in sorted(cases.items()):
        require(entry.get("status") == "PLANNED", f"{case}: not a dry-run plan")
        args = [str(x) for x in entry.get("args", [])]
        declared = [local_path(p, [out], f"{case}.expected_output") for p in entry.get("expected_outputs", [])]
        require(len(declared) == 1, f"{case}: must declare exactly one output")
        actual = []
        ids = []
        if case == "map_export":
            require(len(args) == 7 and args[0] == "render", f"{case}: incorrect render syntax")
            local_path(args[1], [fixtures], f"{case}.input")
            actual.append(local_path(args[2], [out], f"{case}.render_output"))
            require(args[3:] == ["--width", "640", "--height", "480"], f"{case}: wrong PNG render dimensions")
            require(actual[0].suffix == ".png", f"{case}: expected PNG")
        else:
            require(bool(args) and args[0] == "run", f"{case}: CLI subcommand must be run")
            i = 1
            while i < len(args):
                flag = args[i]
                require(flag in {"--data", "--cmd"} and i + 1 < len(args),
                        f"{case}: unsupported or incomplete CLI argument: {flag}")
                value = args[i + 1]
                if flag == "--data":
                    local_path(value, [fixtures, out], f"{case}.data")
                    require(Path(value).suffix in {".geojson", ".gpkg"},
                            f"{case}: use explicit layer.addData for CSV")
                else:
                    require("=" in value, f"{case}: command needs JSON params")
                    name, serialized = value.split("=", 1)
                    require(name in ALLOWED_COMMANDS, f"{case}: unexpected command {name}")
                    try:
                        params = json.loads(serialized)
                    except json.JSONDecodeError as exc:
                        raise PlanFailure(f"{case}: bad CLI command JSON") from exc
                    require(isinstance(params, dict), f"{case}: command parameters must be object")
                    ids.append(name)
                    if name == "gp.run":
                        tool = params.get("tool")
                        require(tool in TOOL_PARAMS, f"{case}: unknown geoprocessing tool {tool}")
                        tool_args = params.get("params")
                        require(isinstance(tool_args, dict) and set(tool_args) <= TOOL_PARAMS[tool],
                                f"{case}: invalid {tool} params")
                        require(all(isinstance(v, (str, int, float, bool)) for v in tool_args.values()),
                                f"{case}: unsupported tool value type")
                        if tool == "countPoints":
                            require(tool_args.get("polygons") == "zones" and tool_args.get("points") == "points",
                                    f"{case}: wrong summarize layer names")
                        if tool == "spatialJoin":
                            require(tool_args.get("target") == "points" and tool_args.get("join") == "zones",
                                    f"{case}: wrong spatial join layers")
                            require(tool_args.get("match") in {"Intersects", "Within"},
                                    f"{case}: unsupported spatial join relation")
                        if tool == "calculateGeometry":
                            require(tool_args.get("input") == "transects", f"{case}: wrong transect layer")
                    elif name == "layer.addData":
                        require(case == "csv_xy_import", f"{case}: unexpected explicit data import")
                        require(params == {"path": str(fixtures / "points.csv"), "name": "csv_points",
                                           "x": "longitude", "y": "latitude", "crs": "EPSG:4326"},
                                f"{case}: CSV columns, CRS and layer name must be explicit")
                    elif name == "share.exportLayer":
                        require("path" in params and set(params) <= {"layer", "path", "crs"},
                                f"{case}: unexpected export parameters")
                        path = local_path(params["path"], [out], f"{case}.export")
                        require(path.suffix in {".geojson", ".gpkg"},
                                f"{case}: unexpected export extension")
                        if path.suffix == ".gpkg":
                            require(params.get("crs") == "EPSG:4326", f"{case}: GeoPackage CRS must be explicit")
                        actual.append(path)
                    elif name == "select.byAttributes":
                        require(params == {"layer": "points", "where": "score IS NULL"},
                                f"{case}: changed missing-value predicate")
                    elif name == "select.layerFromSelection":
                        require(params == {"layer": "points"}, f"{case}: changed selection layer")
                i += 2
            require(ids.count("share.exportLayer") == 1, f"{case}: expected exactly one layer export")
            require(ids.count("layer.addData") == (1 if case == "csv_xy_import" else 0),
                    f"{case}: CSV ingestion must be an explicit command")
        require(actual == declared, f"{case}: output target differs from declaration")
        require(actual[0] not in seen_exports, f"{case}: output path collides with another case")
        seen_exports.add(actual[0])
        reviewed[case] = {"commands": ids, "output": str(actual[0].relative_to(out))}
    return {"status": "PASS", "kind": "offline_cli_command_contract_only",
            "case_count": len(reviewed), "executed": False, "cases": reviewed}
