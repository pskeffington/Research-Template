#!/usr/bin/env python3
"""Independent reference checks for synthetic RustGIS regression fixtures."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

EARTH_RADIUS_M = 6_371_000.0  # RustGIS documents spherical geodesic measurements
HERE = Path(__file__).resolve().parent


class ReferenceFailure(AssertionError):
    """A reference input or its expected scientific invariant was violated."""


def require(condition, message):
    # Unlike Python's `assert`, this is also enforced under `python -O`.
    if not condition:
        raise ReferenceFailure(message)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def by_id(feature_collection):
    rows = feature_collection["features"]
    found = {}
    for f in rows:
        ident = f["properties"]["id"]
        require(isinstance(ident, str) and ident, "feature id is missing or not text")
        require(ident not in found, f"duplicate feature id: {ident}")
        found[ident] = f
    return found


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def haversine_m(a, b):
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))


def length_km(geometry):
    coordinates = geometry["coordinates"]
    paths = [coordinates] if geometry["type"] == "LineString" else coordinates
    return sum(haversine_m(a, b) for path in paths for a, b in zip(path, path[1:])) / 1_000


def count_polygon_parts(geom):
    return 1 if geom.geom_type == "Polygon" else len(geom.geoms)


def count_interior_rings(geom):
    polygons = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    return sum(len(poly.interiors) for poly in polygons)


def reference_assertions(directory, expected_path=HERE / "expected/reference_snapshot.json"):
    """Validate independent intersections, within, lengths and projected coordinates.

    Reference requirements are mandatory, not silently omitted when an optional
    import is absent: missing packages or GPKGs invalidate the reference run.
    """
    import shapely
    from shapely.geometry import shape
    from pyproj import Transformer, Geod, __version__ as pyproj_version
    try:
        import fiona
    except ImportError as exc:
        raise ReferenceFailure("Fiona is required to verify projected GeoPackages") from exc

    expected = load(expected_path)
    names = ["zones", "points", "transects", "missing_points", "topology_cases"]
    layers = {name: load(Path(directory) / f"{name}.geojson") for name in names}
    for name, fc in layers.items():
        require(fc["type"] == "FeatureCollection", f"not a FeatureCollection: {name}")
        require(len(fc["features"]) == expected["feature_counts"][name], f"wrong count: {name}")
        require(len(by_id(fc)) == len(fc["features"]), f"duplicate ids: {name}")

    zones = {key: shape(f["geometry"]) for key, f in by_id(layers["zones"]).items()}
    points = {key: shape(f["geometry"]) for key, f in by_id(layers["points"]).items()}
    for key, geom in {**zones, **points}.items():
        require(geom.is_valid and not geom.is_empty, f"invalid or empty geometry: {key}")

    topologies = {}
    for ident, f in by_id(layers["topology_cases"]).items():
        geom = shape(f["geometry"])
        require(geom.is_valid and not geom.is_empty, f"invalid topology fixture: {ident}")
        topologies[ident] = {"parts": count_polygon_parts(geom), "holes": count_interior_rings(geom)}
    require(topologies == expected["topology_cases"], f"topology fixtures changed: {topologies}")

    observed_intersects = {pid: sorted(zid for zid, z in zones.items() if z.intersects(p))
                           for pid, p in points.items()}
    observed_within = {pid: sorted(zid for zid, z in zones.items() if p.within(z))
                       for pid, p in points.items()}
    require(observed_intersects == expected["joins_intersects"], f"intersects differs: {observed_intersects}")
    require(observed_within == expected["joins_within"], f"within differs: {observed_within}")
    zone_counts = {zid: sum(z.intersects(p) for p in points.values()) for zid, z in zones.items()}
    require(zone_counts == expected["zone_intersect_counts"], f"zone counts differ: {zone_counts}")

    # The CSV is a second encoding of the same synthetic points, not a separate
    # uncontrolled dataset. Check axes, missingness, zero and field provenance.
    csv_path = Path(directory) / "points.csv"
    require(csv_path.is_file(), "required CSV input missing")
    with csv_path.open(newline="", encoding="utf-8") as csv_handle:
        table = csv.DictReader(csv_handle)
        require(table.fieldnames == ["id", "site", "longitude", "latitude", "status", "score", "source_class"],
                "CSV column names/order drifted")
        csv_rows = list(table)
    point_rows = by_id(layers["points"])
    csv_ids = [row["id"] for row in csv_rows]
    require(len(csv_ids) == len(point_rows) and set(csv_ids) == set(point_rows),
            "CSV lost or duplicated point IDs")
    for row in csv_rows:
        source = point_rows[row["id"]]
        require(row["site"] == source["properties"]["site"], f"CSV site changed: {row['id']}")
        require(row["source_class"] == "synthetic", f"CSV provenance changed: {row['id']}")
        require([float(row["longitude"]), float(row["latitude"])] == source["geometry"]["coordinates"],
                f"CSV source coordinate drift: {row['id']}")
        expected_status = source["properties"]["status"]
        expected_score = source["properties"]["score"]
        require(row["status"] == ("" if expected_status is None else expected_status),
                f"CSV missing/status value drift: {row['id']}")
        require(row["score"] == ("" if expected_score is None else str(expected_score)),
                f"CSV missing/zero score drift: {row['id']}")

    null_geom = sorted(k for k, f in by_id(layers["missing_points"]).items() if f["geometry"] is None)
    require(null_geom == expected["expected_null_geometry_ids"], f"null geometries differ: {null_geom}")
    null_score = sorted(k for k, f in by_id(layers["points"]).items() if f["properties"]["score"] is None)
    require(null_score == sorted(expected["expected_null_attribute_ids"]), f"null scores differ: {null_score}")

    geod = Geod(ellps="WGS84")
    lengths, ellipsoid_lengths = {}, {}
    for ident, feature in by_id(layers["transects"]).items():
        geometry = feature["geometry"]
        lengths[ident] = length_km(geometry)
        segments = [geometry["coordinates"]] if geometry["type"] == "LineString" else geometry["coordinates"]
        ellipsoid_lengths[ident] = sum(abs(geod.inv(a[0], a[1], b[0], b[1])[2])
                                        for line in segments for a, b in zip(line, line[1:])) / 1_000
        require(abs(lengths[ident] - ellipsoid_lengths[ident]) < 0.01,
                f"unexpected spherical/ellipsoidal discrepancy: {ident}")
        require(abs(lengths[ident] - expected["reference_spherical_lengths_km"][ident]) < 1e-8,
                f"spherical fixture drift: {ident}")

    gpkg_checks = {}
    originals = by_id(layers["points"])
    for site, epsg in expected["projected_crs"].items():
        input_path = Path(directory) / f"points_{site.lower()}_{epsg.split(':')[-1]}.gpkg"
        require(input_path.is_file(), f"required projected GPKG missing: {input_path.name}")
        tr = Transformer.from_crs(epsg, "EPSG:4326", always_xy=True)
        checked = 0
        observed_ids = set()
        with fiona.open(input_path) as ds:
            require(ds.crs is not None and ds.crs.to_epsg() == int(epsg.split(":")[1]),
                    f"wrong source CRS: {site}")
            for feat in ds:
                ident = feat["properties"]["id"]
                require(ident in originals and ident not in observed_ids,
                        f"unexpected or duplicate GPKG id: {ident}")
                observed_ids.add(ident)
                require(originals[ident]["properties"]["site"] == site, f"cross-site GPKG id: {ident}")
                x, y = feat["geometry"]["coordinates"]
                lon, lat = tr.transform(x, y)
                original = originals[ident]["geometry"]["coordinates"]
                error_m = abs(geod.inv(lon, lat, *original)[2])
                require(math.isfinite(error_m) and error_m <= expected["projected_roundtrip_tolerance_m"],
                        f"projected source error {ident}: {error_m} m")
                checked += 1
        expected_ids = {ident for ident, feat in originals.items()
                        if feat["properties"]["site"] == site and "EDGE" not in ident}
        require(checked == 4 and observed_ids == expected_ids,
                f"wrong GPKG row/ID inventory {site}: {sorted(observed_ids)}")
        gpkg_checks[site] = {"checked": checked, "epsg": epsg}

    return {
        "status": "PASS",
        "source": "independent Shapely + pyproj geospatial oracle (Fiona for GPKG)",
        "reference_library_versions": {"shapely": shapely.__version__, "pyproj": pyproj_version,
                                       "fiona": fiona.__version__},
        "counts": expected["feature_counts"],
        "zone_counts": zone_counts,
        "csv_point_integrity": {"ids_checked": len(csv_ids), "status_and_score_checked": True,
                                "columns_checked": True},
        "join_matches": observed_intersects,
        "within_matches": observed_within,
        "topology_cases": topologies,
        "spherical_line_lengths_km": {k: round(v, 9) for k, v in lengths.items()},
        "ellipsoidal_line_lengths_km": {k: round(v, 9) for k, v in ellipsoid_lengths.items()},
        "projected_gpkg_checks": gpkg_checks,
        "sha256": {p.name: hash_file(p) for p in sorted(Path(directory).iterdir()) if p.is_file()},
    }


def main():
    import argparse
    from generate_fixtures import generate
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--directory", type=Path, default=HERE / "generated")
    ap.add_argument("--skip-generation", action="store_true")
    args = ap.parse_args()
    if not args.skip_generation:
        generate(args.directory)
    print(json.dumps(reference_assertions(args.directory), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
