# Contributing and Git protocol

**Author: Paul Skeffington · Prepared with OpenAI**

Open a short-lived branch from `main`. Keep one scientific/software purpose per pull request and use concise commit messages (e.g., `test: reject duplicate participant keys`, `feat: add independent plotting wrapper`). Explain the scientific rationale, data schema and units, test evidence, numerical or figure changes, release implications and limitations.

Before requesting review: `python -m pip install -e '.[all]'`, `ruff check .`, `pytest -q`, `research-template demo --plots --ml`, `research-template audit --root .`. Optional R tests require a separately installed R runtime and ggplot2. Document version changes and regenerate checksums for derived scientific output. Never commit PHI, identifiable examples, internal organization source materials, passwords, model weights, restricted datasets or secrets. `.gitignore` is a convenience, **not** a security boundary; inspect staged content with `git diff --cached --name-only` and `git diff --cached`.

Reviewer gates: (1) code correctness and tests, (2) schema and provenance, (3) appropriate methodology and split isolation, (4) figure labels and interpretation, (5) explicit release authorization. Configure branch protection / required CI / minimum reviewers in GitHub Settings. Deployment requires a separate approved PR or signed release, not an ordinary push to `main`.

## R style and tidyverse validation

Follow [R/STYLE_GUIDE.md](R/STYLE_GUIDE.md): snake_case internal names, native `|>`, namespaced `dplyr`/`tidyr`/`ggplot2`, complete units and no source-time side effects. Confirm `Rscript --vanilla R/tests/test_style_contract.R`, `Rscript --vanilla R/tests/test_tidy_workflow.R`, and `Rscript --vanilla R/tests/test_research_plots.R` all pass before merging. Do not substitute style for data integrity or clinical evidence.

## Complete repository style checks

Before merging run `ruff check .`, `python -m pytest -q`, `Rscript --vanilla R/tests/test_style_contract.R`, `Rscript --vanilla R/tests/test_documentation_examples.R`, `Rscript --vanilla R/tests/test_tidy_workflow.R` and `Rscript --vanilla R/tests/test_research_plots.R`. The [coding conventions](docs/CODING_CONVENTIONS.md) apply to all source files, not just the original examples. Preserve external variable names, identifiers, units and analysis semantics.

## New researcher onboarding

Changes to study initialization or the five-minute guide must retain synthetic-only tests for safe destination handling, case preservation, symlinks, source-register headers and false publication approvals. Verify init-study and check-study in CI before merging. Generated study workspaces under artifacts/ must remain ignored, and installing the Python core cannot depend on R or ML extras.
