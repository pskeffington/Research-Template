# Data dictionary and joining contract

**Current sample: synthetic only. Replace before using real data.**

| Variable | Type | Unit / allowed values | Missing | Unique / join rule |
| --- | --- | --- | --- | --- |
| participant_id | string | SIM-xxxxx fabricated identifier | not allowed | Unique synthetic participant key |
| site | string | North, South, West (invented categories) | not allowed | Descriptive only |
| age_years | numeric | years (simulated range, not a reference interval) | allowed, null | One synthetic adult per row |
| measurement_mg_dl | numeric | mg/dL (invented biomarker) | allowed, null | One measurement per person |
| outcome | int | 0 or 1 simulated label | not allowed | No clinical meaning |

**Contracts:** validate types without implicit coercion; preserve missingness; reject duplicate IDs; maintain explicit row-level unit and ID semantics. For longitudinal data, explicitly model repeated participant IDs and visit keys rather than bypassing duplicate checks. Maintain a source-to-internal-name crosswalk and join cardinality proof. Never infer that a similarly named real source column uses the same units.

New study dictionary fields: source variable, unit, missing codes/reasons, range, controlled vocabulary, derivation, measurement date, transformation, provenance, confidentiality class, and release permission.

## Source-to-analysis name preservation

The normalized columns in this table are internal schema choices. The runnable [tidyverse workflow](../R/example_tidy_workflow.R) deliberately retains synthetic source field names (`Subject_ID`, `Age`, `Site`, `Marker`) before applying the explicit mapping to `participant_id`, `age_years`, `site`, `measurement_mg_dl`. Never silently rename accession IDs, NHANES variable names, external standards or repeated visit keys.
