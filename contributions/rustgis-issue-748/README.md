# RustGIS issue #748 — synthetic geospatial CLI tests

This is the public review staging area for a tested, additive contribution to [opengeos/RustGIS issue #748](https://github.com/opengeos/RustGIS/issues/748). The user account has no upstream write access and no RustGIS fork. This is **not yet an upstream PR**.

- [Exact validated Git-apply patch](rustgis_issue_748_synthetic_field_validation.patch), SHA-256 `316f55c2247037334bb4510ceaed5a099da6bf4b4157d4acddd1291eef84e710`
- [Browse the 13 proposed upstream test files](tests/field_validation/README.md)
- [Source SHA-256 manifest](SOURCE_SHA256_MANIFEST.json) and [submission instructions](SUBMISSION_NOTES.md)
- [Public verification workflow](../../.github/workflows/rustgis-issue-748-validation.yml)

### Already executed

- RustGIS v0.4.0 official CLI: **16/16 synthetic engine cases PASS**.
- Source-built RustGIS `f3aaf35de7db4f1c394c7b69e314b0322fe6b3ec`, Ubuntu 24.04, Rust 1.95: **16/16 synthetic cases PASS** and **8/8 separate public McDowell interchange cases PASS**, with zero observed semantic drift from v0.4.0.
- The owned full regression suite: **174/174 Python tests PASS**. The 37 upstream-neutral tests are included here.
- The public workflow verifies patch applicability to newer upstream source commit `c7bf8e1f9ebe82d25ee56f76a1aa6c43b4cd98ec`. It does **not** claim a compiled CLI run from that newer revision.

**Data boundary:** All included test features are generated fictionally. No resident, utility-service boundary, public McDowell GIS feature, source document, credential or private file is included. Four optional Python libraries (Shapely, pyproj, Fiona, Pillow); no Rust/Cargo dependency changes.

### Apply and run in a RustGIS checkout

```sh
curl -fLsS https://raw.githubusercontent.com/pskeffington/Research-Template/main/contributions/rustgis-issue-748/rustgis_issue_748_synthetic_field_validation.patch -o rustgis-748.patch
git apply --check --whitespace=error rustgis-748.patch
git apply rustgis-748.patch
python -m pip install -r tests/field_validation/requirements-reference.txt
python -m unittest discover -s tests/field_validation/tests -v
python tests/field_validation/run_validation.py --offline --out /tmp/rustgis-748-offline
python tests/field_validation/run_validation.py --cli /path/to/rustgis-cli --require-cli --out /tmp/rustgis-748-engine
```

The offline oracle is **not** an engine run. Tests cover spatial joins/boundaries, CSV XY input, projected CRSs, null/missing geometry, geodesic lengths, multipart/hole fidelity, GeoJSON/GeoPackage round trips and headless PNG export. They do not cover GUI, GPU, raster workflows, cloud data, database connections or project migration. The public Research-Template repository is MIT licensed.
