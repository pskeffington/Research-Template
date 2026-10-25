# RustGIS synthetic field-validation pack

**Testing topic:** https://github.com/opengeos/RustGIS/issues/748

An optional, additive Python harness for the RustGIS CLI, with deterministic,
entirely invented GIS fixtures. There are no original McDowell County records,
utility service boundaries, household data, credentials or live data pulls.

The 16 engine cases cover projected/CSV input, spatial joins and boundaries,
null/missing geometry, geodesic length, GeoJSON/GeoPackage round trips, polygon
holes/multipart cases, and map PNG export. Independent scientific references
are separate from RustGIS results.

## Exact 16-case executable coverage

| Group | CLI cases | Count |
| --- | --- | ---: |
| Polygon point counts and spatial-join predicates | summarize_within; spatial_join; spatial_join_within | 3 |
| Geodesic line measurement | geodesic_lengths | 1 |
| CSV XY import and null-value selection | csv_xy_import; null_attribute_filter | 2 |
| GeoJSON/GeoPackage bidirectional fidelity | zones_geojson_to_gpkg; zones_gpkg_to_geojson; transects_geojson_to_gpkg; transects_gpkg_to_geojson; topology_cases_geojson_to_gpkg; topology_cases_gpkg_to_geojson | 6 |
| Projected CRS back to WGS84 | projected_ply; projected_mcd | 2 |
| Missing-geometry behavior | missing_geometry | 1 |
| Headless PNG map export | map_export | 1 |
| **TOTAL** | **16 executable cases** | **16** |

**Not covered by these 16 cases:** desktop editing or GUI accessibility,
saved-project migration, raster/georeferencing, 3D or GPU interaction,
PostGIS/SQL connections, STAC/cloud sources, time cubes, or
platform-specific macOS/Windows packaging. The test report makes no
claim about those areas or about geographic source authority.

## Run from the RustGIS repository root

~~~sh
python -m pip install -r tests/field_validation/requirements-reference.txt
python -m unittest discover -s tests/field_validation/tests -v
python tests/field_validation/run_validation.py --offline --out /tmp/rustgis-oracle
python tests/field_validation/run_validation.py --plan-only --out /tmp/rustgis-plan
python tests/field_validation/run_validation.py --cli /path/to/rustgis-cli --require-cli --out /tmp/rustgis-engine
~~~

A passing offline oracle or command plan is NOT a RustGIS engine execution.
If the actual executable is required and unavailable, the harness reports
SKIPPED (exit 2); missing or corrupt executable output fails closed.

## Pinned executed evidence (October 25, 2026)

- v0.4.0 release commit 25bf787f99d3ca10cf2281f5b7159292757a3236:
  16/16 synthetic CLI cases passed (https://github.com/pskeffington/McDowell-County-Commission-on-Aging-Inc./actions/runs/40165488469).
- Previously pinned development commit
  2aaa0f06eaabc852270c89dcd507afa8a17bfb1c:
  16/16 synthetic CLI cases passed, with 8/8 additional public-source
  fidelity cases in a SEPARATE owned workflow (https://github.com/pskeffington/McDowell-County-Commission-on-Aging-Inc./actions/runs/40166057195).
  No public source features are in this contribution.
- The later upstream tree at f3aaf35de7db4f1c394c7b69e314b0322fe6b3ec
  is the independently checked patch applicability target. Newer upstream
  executable verification must be cited separately with its exact CI run.

The suite introduces no new Rust dependency, engine API, UI change, or command
identifier. The standalone optional suite depends only on Shapely, pyproj,
Fiona and Pillow; the McDowell-specific pandas/geopandas/YAML dependencies
are deliberately excluded. Fixtures are generated at runtime.
