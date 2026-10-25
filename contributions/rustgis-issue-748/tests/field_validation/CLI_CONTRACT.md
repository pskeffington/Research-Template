# Local RustGIS CLI contract audit — 2026-10-25

**No repository mutations, commits, pushes, pull requests, issues or upstream comments.** This is source-informed validation planning only. No RustGIS executable was available locally, and outbound network/DNS access was unavailable in the development container. Consequently, any CLI integration result must remain `SKIPPED` until executed on an actual versioned RustGIS binary.

## Evidence chronology

The source-only statement above describes the **initial local contract
review**, before a RustGIS executable was available to that local container.
Subsequent, independently executed GitHub Actions runs in the owned McDowell
repository successfully tested the real official **v0.4.0 CLI on 16/16
synthetic cases** (run 40220041808), and independently compiled an earlier
development commit `2aaa0f06` for comparison (run 40166057195).
The newer source commit `f3aaf35d` must be assessed by its **own** executed
development-build workflow; applying a source patch does not establish
executable compatibility. No upstream changes were submitted.

## Reviewed upstream sources

The precise GitHub file blob SHA observations and latest head observed during the read-only review are recorded in `expected/upstream_cli_contract.json`. The signatures used here were checked directly against:

- [CLI implementation](https://github.com/opengeos/RustGIS/blob/main/apps/rustgis-cli/src/main.rs): `run --data` loads a file via `layer.addData`; repeated `--cmd 'id={...}'` invokes engine commands in order; `render INPUT OUTPUT --width ... --height ...` supports image export.
- [Layer commands](https://github.com/opengeos/RustGIS/blob/main/crates/engine/src/cmd/layer.rs): `layer.addData` takes `path`, `name`, explicit `x`, `y` and `crs` for CSV. The project distinguishes feature layers from non-spatial tables.
- [Data reader](https://github.com/opengeos/RustGIS/blob/main/crates/data/src/io.rs): CSV import accepts explicit x/y fields, infers column types, and treats invalid coordinates separately from missing attributes.
- [Geoprocessing adapter](https://github.com/opengeos/RustGIS/blob/main/crates/engine/src/cmd/gp.rs): `gp.run` accepts `tool` and `params` and applies a geoprocessing result.
- [Geoprocessing tool definitions](https://github.com/opengeos/RustGIS/blob/main/crates/analysis/src/tools.rs): `countPoints`, `spatialJoin`, `calculateGeometry` have the parameters listed in the local allowlist.
- [Export commands](https://github.com/opengeos/RustGIS/blob/main/crates/engine/src/cmd/share.rs): `share.exportLayer` writes GeoJSON or GeoPackage, and `share.exportMap` exports PNG.

### Why the CLI plan changed

v1.1 loaded `points.csv` using the `--data` convenience option. Although the RustGIS reader currently recognizes common XY column names, that leaves the test sensitive to importer heuristics and defaults. v1.2 uses an explicit command instead:

```sh
rustgis-cli run \
  --cmd 'layer.addData={"path":"<synthetic-fixture>/points.csv","name":"csv_points","x":"longitude","y":"latitude","crs":"EPSG:4326"}' \
  --cmd 'share.exportLayer={"layer":"csv_points","path":"<local-results>/csv_points.geojson"}'
```

The path placeholders in the example are **illustrative**. Actual file paths are computed at runtime within the local synthetic workspace.

## Offline plan audit

Run with the same Python dependencies as the reference suite:

```sh
python run_validation.py --plan-only --out results/local_plan
```

This regenerates synthetic inputs and checks all 16 intended RustGIS CLI invocations without executing the CLI. `cli_plan.py` rejects unrecognized commands/tools, unsupported arguments, changed CSV axis/CRS settings, output collisions, nonlocal output destinations, network/URI paths, and mismatches between declared output and command output. Commands and their expected output paths are emitted in `validation_report.json` under `engine_plan`.

A successful audit sets `engine_plan.status=PASS` and **`engine_status=SKIPPED`**. It is not a substitute for an actual program run, a Rust compile, or integration testing.

## Independent input/output gates

1. **Reference inputs:** Shapely + pyproj evaluate intersections, within, geodesic distances, holes/multipart; Fiona validates projected GeoPackages; CSV rows are checked against GeoJSON for IDs, coordinates, nulls, zeroes and provenance.
2. **GeoPackage intermediate:** Fiona independently opens the newly exported GPKG before RustGIS reimports it, requiring EPSG:4326, consistent feature inventory, attributes, geometry topology and coordinates.
3. **Operation outputs:** Spatial join checks target geometries and fields, join fields/metadata, cardinality and matched IDs. Summarize-within checks source polygons as well as counts. Calculate-geometry checks the original lines as well as lengths. CSV checks points and attributes, not only IDs/coordinates. Missing-geometry checks retained metadata or an explicit exclusion notice.
4. **Negative controls:** Unit tests deliberately change coordinates, join attributes, CRS labels, null/zero values, tool names, CLI axis mappings and output paths; the comparators must reject these.

## The later RustGIS execution gate (not performed)

From a machine with the **real** RustGIS CLI installed, outside any fake-CLI test directory:

```sh
python run_validation.py --cli /path/to/rustgis-cli --require-cli --out results/actual_rustgis
```

Record the exact RustGIS version and source commit from the binary build, Python/Fiona/pyproj/Shapely versions, operating system and per-test stdout/stderr. Do not generalize a source-based contract check into a successful RustGIS integration claim. `rustgis-cli` must be tested against a known build and issues reported with minimized synthetic reproductions only.
