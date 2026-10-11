# Set up a new research project

Use this as a working procedure, not a substitute for a study-specific approved protocol.

1. **Frame the question.** Define population, observation unit, predictor/exposure, outcome, time horizon, purpose and whether the objective is descriptive, inferential or predictive.
2. **Document inputs.** Complete [SOURCE_REGISTER.md](SOURCE_REGISTER.md) and [DATA_DICTIONARY.md](DATA_DICTIONARY.md); list licenses, privacy classifications, rights and allowed joins. Do not add restricted data to Git.
3. **Freeze decisions.** Fill [PROTOCOL.md](PROTOCOL.md) before analysis; identify groups/time structure, sampling/survey weights, measurement units, missingness rules, exclusions and planned tests.
4. **Prepare environments.** Create a Python 3.11+ virtual environment and install declared extras, optionally establish a project-specific lockfile (e.g. pip-tools/uv) with reviewed hashes; record Python/R and OS versions. For R, use `renv::init()` in the downstream project only after reviewing dependency licenses.
5. **Run the smoke tests.** Execute `pytest -q` and `research-template demo --plots --ml`. Any provided demo results are synthetic and must remain marked as such.
6. **Replace contracts, not just data.** Add data ingestion only after access approval and schema tests for types, missingness, duplicate keys, join cardinality and time leakage. Real data generally belongs in controlled storage outside this public Git history.
7. **Promote exploratory logic.** Move stable notebook code into `src/` or `R/` with deterministic entry points and negative tests. Avoid relying on notebook execution order.
8. **Separate evidence from release.** Record run parameters, code revision, input/output checksums, figure captions, denominators and source claims; use [RELEASE_GATES.md](RELEASE_GATES.md) for documented scientific decisions.

Environment installation is *not* itself data access, scientific review, or permission to deploy.

## R/tidyverse execution style

Use [R/STYLE_GUIDE.md](../R/STYLE_GUIDE.md). Keep external source names unchanged; normalize with `rename_source_columns()` only after documenting the mapping. Audit IDs and joins before `dplyr` transformations. Use `tidyr::pivot_longer()` and `pivot_wider()` via row-count and unit-validated wrappers; summarize with `summarize_measurements()` and `summarize_missingness()`. Build figures as editable layered `ggplot2` objects and save only intentionally.
