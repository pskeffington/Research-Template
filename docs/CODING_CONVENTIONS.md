# Whole-repository coding conventions

**Author: Paul Skeffington · Prepared with OpenAI**

This starter uses R-first biomedical research workflows and complementary Python
machine learning. Use **each language's established idioms** rather than
transliterating tidyverse syntax into Python.

## R: tidyverse and layered ggplot2

The [R style contract](../R/STYLE_GUIDE.md) is grounded in the public
[local R style guide](../R/STYLE_GUIDE.md).
Use snake_case for newly authored functions and internal columns,
native `|>` pipelines, explicit `dplyr::`, `tidyr::`, `tibble::`
and `ggplot2::` namespaces, and `.data[[column]]` for dynamic
aesthetics.

Preserve source variable names, units, accession IDs and external data
contracts in the raw layer. Translate names only through a documented
source-to-analysis mapping with identity and join-cardinality checks. Do not
coerce missing values to measured zeros. Give every figure a meaningful
title, unit-bearing axes, denominator, caption and evidence status.
Return editable ggplot objects rather than writing plots during imports.

Reusable R modules may only define functions or the existing explicit
`rt_make_synthetic` compatibility alias when sourced. File I/O must be a
named action. R test scripts are separate executable entry points.

For algorithms and foundational language behavior, see [the 20-method `caret` algorithm index](CARET_ALGORITHM_CATALOG.md) and [essential R programming mechanics](R_PROGRAMMING_MECHANICS.md). Runtime introspection uses original `R/caret_algorithm_catalog.R` functions and a version-pinned official method source, never arbitrary unreviewed downloaded code. A catalog audit verifies model *metadata* only; it does not certify 20 executable biomedical classifiers.

## Python: PEP 8 and research software contracts

Use snake_case for Python functions, variables and files, and PascalCase
for classes. Keep type hints, portable pathlib paths, explicit imports,
and optional heavy dependencies lazy. Follow the repository's
[`pyproject.toml`](../pyproject.toml) Ruff checks.

Python ML routines must isolate training preprocessing, declare prediction
horizons and grouped/time splits, compare meaningful baselines and record
seed and package versions. Python plotting helpers retain scientific
labels, complete-case n, missingness and source limitations.

Do not require Python users to write `dplyr` or use R pipes. The
repository treats R as the primary teaching presentation for biomedical
tabular operations, not as the only supported analysis language.

## GitHub workflow, scripts, documentation and data boundaries

- Scripts should be idempotent or state side effects explicitly; do not
  download data, install packages or deploy on module import.
- YAML uses two-space indentation; CI permissions remain read-only
  unless explicitly reviewed.
- R and Python examples in Markdown must use the same import/source order
  as executable code and be parseable where shown as complete examples.
- No patient identifiers, credentials, restricted datasets or
  model weights are committed to this public template.

**Permanent enforcement:** CI discovers every `R/**/*.R` file,
parses R sources, checks source-time safety, snake_case function names,
native pipes and explicit tidyverse namespaces. Python Ruff and
AST-based naming checks cover all Python packages, scripts and tests.
The synthetic R/Python regression suites verify numerical semantics.
No blanket rename applies to external datasets or standard APIs.
