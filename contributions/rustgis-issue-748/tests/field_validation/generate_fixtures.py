#!/usr/bin/env python3
"""Generate entirely synthetic, deterministic GIS fixtures (no agency or resident data)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SITES = {
    "PLY": {"label": "Plymouth-inspired synthetic", "epsg": "EPSG:26986"},
    "MCD": {"label": "McDowell-inspired synthetic", "epsg": "EPSG:26917"},
}
BOXES = {
    "PLY-A": (-70.72, 41.94, -70.68, 41.97),
    "PLY-B": (-70.68, 41.94, -70.64, 41.97),
    "MCD-A": (-81.64, 37.35, -81.60, 37.38),
    "MCD-B": (-81.60, 37.35, -81.56, 37.38),
}
POINTS = [
    ("PLY-01", "PLY", -70.71, 41.950, "observed", 3.0),
    ("PLY-02", "PLY", -70.70, 41.960, "review", 1.0),
    ("PLY-03", "PLY", -70.67, 41.950, None, None),
    ("PLY-04", "PLY", -70.63, 41.960, "unassigned", 0.0),
    ("PLY-EDGE", "PLY", -70.68, 41.955, "boundary", 2.0),
    ("MCD-01", "MCD", -81.63, 37.360, "observed", 4.0),
    ("MCD-02", "MCD", -81.62, 37.370, "review", None),
    ("MCD-03", "MCD", -81.58, 37.360, "observed", 2.0),
    ("MCD-04", "MCD", -81.55, 37.360, "unassigned", 0.0),
    ("MCD-EDGE", "MCD", -81.60, 37.360, "boundary", 1.0),
]
TRANSECTS = [
    ("PLY-L1", "LineString", [[-70.71, 41.95], [-70.70, 41.95]]),
    ("PLY-L2", "MultiLineString", [
        [[-70.70, 41.951], [-70.69, 41.951]],
        [[-70.69, 41.952], [-70.68, 41.952]],
    ]),
    ("MCD-L1", "LineString", [[-81.63, 37.36], [-81.63, 37.37]]),
]


def rectangle(bbox):
    west, south, east, north = bbox
    return [[west, south], [east, south], [east, north], [west, north], [west, south]]


def collection(features):
    return {"type": "FeatureCollection", "features": features}


def feature(ident, geometry, **props):
    return {"type": "Feature", "properties": {"id": ident, **props}, "geometry": geometry}


def build():
    zones = collection([
        feature(name, {"type": "Polygon", "coordinates": [rectangle(box)]},
                site=name[:3], zone_id=name, source_class="synthetic", authority="none")
        for name, box in BOXES.items()
    ])
    points = collection([
        feature(ident, {"type": "Point", "coordinates": [lon, lat]},
                site=site, status=status, score=score, source_class="synthetic")
        for ident, site, lon, lat, status, score in POINTS
    ])
    transects = collection([
        feature(ident, {"type": kind, "coordinates": coords}, source_class="synthetic")
        for ident, kind, coords in TRANSECTS
    ])
    missing = collection([
        feature("NULL-01", None, site="PLY", status="missing_geometry", score=None),
        feature("NULL-02", {"type": "Point", "coordinates": [-70.707, 41.958]},
                site="PLY", status=None, score=None),
    ])
    # A deliberate interior hole and a two-part geometry expose false-positive
    # comparators that only look at bounding boxes or external ring distances.
    topology = collection([
        feature("PLY-HOLE", {"type": "Polygon", "coordinates": [
            rectangle((-70.717, 41.945, -70.705, 41.957)),
            list(reversed(rectangle((-70.713, 41.948, -70.709, 41.954)))),
        ]}, site="PLY", source_class="synthetic", claim="non-authoritative"),
        feature("MCD-MULTI", {"type": "MultiPolygon", "coordinates": [
            [rectangle((-81.637, 37.355, -81.630, 37.362))],
            [rectangle((-81.615, 37.366, -81.608, 37.373))],
        ]}, site="MCD", source_class="synthetic", claim="non-authoritative"),
        feature("PLY-SINGLE", {"type": "Polygon", "coordinates": [
            rectangle((-70.695, 41.946, -70.688, 41.953))
        ]}, site="PLY", source_class="synthetic", claim="non-authoritative"),
    ])
    # Geometry promotions are expected when writing some GPKG tables.
    return {"zones.geojson": zones, "points.geojson": points,
            "transects.geojson": transects, "missing_points.geojson": missing,
            "topology_cases.geojson": topology}


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_projected_gpkg(output_dir: Path):
    """Create projected GPKG inputs with an independent pyproj/Fiona pipeline."""
    try:
        import fiona
        from pyproj import Transformer
    except ImportError as exc:
        raise RuntimeError("Projected GPKG generation requires fiona and pyproj") from exc
    for site, meta in SITES.items():
        path = output_dir / f"points_{site.lower()}_{meta['epsg'].split(':')[-1]}.gpkg"
        if path.exists():
            path.unlink()
        tr = Transformer.from_crs("EPSG:4326", meta["epsg"], always_xy=True)
        schema = {"geometry": "Point", "properties": {"id": "str:32", "site": "str:8", "status": "str:30", "score": "float"}}
        with fiona.open(path, "w", driver="GPKG", layer="synthetic_points", schema=schema,
                        crs=meta["epsg"]) as dst:
            for ident, row_site, lon, lat, status, score in POINTS:
                if row_site != site or "EDGE" in ident:
                    continue  # boundary precision is tested in the original EPSG:4326 input
                x, y = tr.transform(lon, lat)
                dst.write({"type": "Feature", "properties": {
                    "id": ident, "site": row_site, "status": status, "score": score},
                    "geometry": {"type": "Point", "coordinates": (x, y)}})
    return 2


def generate(output_dir: Path, with_gpkg: bool = True):
    output_dir.mkdir(parents=True, exist_ok=True)
    data = build()
    for filename, content in data.items():
        write_json(output_dir / filename, content)
    with (output_dir / "points.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "site", "longitude", "latitude", "status", "score", "source_class"])
        for ident, site, lon, lat, status, score in POINTS:
            writer.writerow([ident, site, lon, lat, status if status is not None else "",
                             score if score is not None else "", "synthetic"])
    if with_gpkg:
        write_projected_gpkg(output_dir)
    return output_dir


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "generated")
    ap.add_argument("--no-gpkg", action="store_true", help="omit projected GeoPackages, leaving a stdlib-only generator")
    args = ap.parse_args()
    print(generate(args.output, with_gpkg=not args.no_gpkg))
