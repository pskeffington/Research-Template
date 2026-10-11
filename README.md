# Research Template — Reproducible Biomedical Research Starter

**Author: Paul Skeffington · Prepared with OpenAI**

A reusable, independently written starter repository for biomedical data science, reproducible research, scientific figures, baseline machine learning, and auditable delivery. Everything in the demonstration is **synthetic**. It does not represent patient records, clinical evidence, regulatory qualification, or production-grade diagnostic software.

## R/tidyverse coding standard — preferred for biomedical studies

The R research workflow follows the [whole-repository coding contract](docs/CODING_CONVENTIONS.md), [independent biomedical coding conventions](https://github.com/pskeffington/Dartmouth.HSE.Public/blob/main/06_RESOURCES/Literature/BIOMEDICAL_CODING_STANDARDS.md), the [R style contract](R/STYLE_GUIDE.md), and the [complete R function sheet](R/README.md). It preserves original source names, uses snake_case analysis fields, explicit native `|>` with `dplyr` and `tidyr`, audited join cardinality, clear missing-value denominators, and layered `ggplot2` grammar.

```r
source("R/research_tidy.R")
source("R/research_plots.R")
source("R/synthetic_demo.R")
source("R/example_tidy_workflow.R")
result <- run_tidy_example()
print(result$join_audit)
print(result$site_summary)
print(result$figure)
```

R 4.1+, `ggplot2`, `dplyr`, `tidyr` and `tibble` are required for this optional R workflow; CI installs them. `readr` is available for explicitly approved CSV imports. There are no downloads or writes when R files are sourced.

## Python quick start (parallel workflow)

**Python 3.11+**, Git, and an internet connection for the first dependency installation are required. R is optional.

```bash
git clone https://github.com/pskeffington/Research-Template.git
cd Research-Template
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[all]'
pytest -q
research-template demo --out artifacts/demo --plots --ml
research-template audit --root .
```

The run generates synthetic CSV data, numeric and grouped summary-statistics tables (n, missing values, mean, SD, median, quartiles, IQR, range), nine publication-oriented PNG/PDF figure presets with JSON provenance/checksums, baseline ML metrics and a run manifest in `artifacts/demo/` (gitignored). Run without optional packages via `python -m pip install -e .` and `research-template demo`. Audit verifies the scaffold, **not scientific validity**; `research-template audit --require-release` intentionally fails until a specific study passes independent scientific review.

## Find the right tool

| Goal | Start here | Ready-to-call interface |
| --- | --- | --- |
| Coding conventions | **[Whole-repository style contract](docs/CODING_CONVENTIONS.md)** and [R style guide](R/STYLE_GUIDE.md) | GitHub CI enforces both R and Python conventions |
| Configure a study | [Project setup](docs/PROJECT_SETUP.md), [protocol](docs/PROTOCOL.md), [data dictionary](docs/DATA_DICTIONARY.md) | `research-template audit --root .` |
| Find a function | **[Complete biomedical R/Python function sheet](docs/FUNCTION_CALL_SHEET.md)** | `FigureKit`, `kit.summary()`, `kit.box()`, `kit.correlation_heatmap()` |
| Produce scientific figures | [Colors, heatmaps and complete figure conventions](docs/FIGURE_STANDARD.md) | `kit.histogram()`, `kit.missingness()`, `FigureKit.matrix_heatmap()` |
| Start statistical comparison | [Statistical workflow](docs/STATISTICAL_WORKFLOW.md) | R comparison/test recipe with explicit assumptions |
| Develop a prediction model | [ML playbook](docs/ML_PLAYBOOK.md) | `run_classification()`, optional PyTorch |
| Track evidence | [Source register](docs/SOURCE_REGISTER.md), [literature matrix](references/LITERATURE_MATRIX.csv) | `create_manifest()`, `sha256_file()` |
| Release a defensible result | [Release gates](docs/RELEASE_GATES.md) | G0–G5 review and separate deployment permission |
| Use Git / review PRs | [Contributing](CONTRIBUTING.md) | Branch → test → PR → reviewed merge |
| Run R examples | **[Tidyverse R companion](R/README.md)** and [style guide](R/STYLE_GUIDE.md) | `source("R/research_tidy.R")`; `run_tidy_example()` |

## Included capabilities

- **Python core:** zero mandatory runtime dependencies, validated synthetic example, explicit units, missingness and duplicate-key checks, manifest with Git revision, environment versions, SHA-256 outputs.
- **Figures and summaries:** dictionary-driven `FigureKit` declares units and study provenance once, then builds full-axis histograms, boxes, violins, grouped scatters, counts, missingness, Pearson correlation matrices and both heatmap types. Matching R companion, one-call mean/SD/median/IQR/group statistics, category-safe Okabe–Ito colors, Viridis magnitude, centered RdBu diverging heatmaps, missing-gray and 300 dpi PNG/vector PDF + JSON figure trace.
- **Machine learning:** optional scikit-learn group-preserving holdout, training-only imputation/scaling, logistic regression versus dummy baseline, balanced accuracy, AUROC and Brier score. An additional CPU PyTorch example is opt-in.
- **R companion:** R-first tidyverse syntax with `dplyr`, `tidyr`, tibble summaries, native pipes, audited joins and editable `ggplot2` figures. Nothing installs packages or writes files merely when sourced.
- **Governance:** CI, tests, PR checklist, no automatic deployment, data boundary, literature matrix, project protocol and scientific gates.

## Research workflow

`question → literature review → protocol → rights/source register → validate & transform → descriptive analysis → baseline ML (when justified) → figures & statistics → human scientific review → gated release`

Git history and passing CI establish software traceability, not automatically publishable scientific conclusions. Secure clinical datasets, credentials, private model weights, licensed source files and identifiable outputs must **never** be added to this public template. Adapt the data contract to each actual project rather than assuming the synthetic contract applies.

## Make your own project

To create an independent repository from this starter, the repository owner must first enable the GitHub **Template repository** setting. Once enabled, use **Use this template → Create a new repository**. Until then, clone it normally. Replace sample study documents, update `pyproject.toml`, adjust schema and CI, and record authorization before reading real data. Do not treat the shared default branch as a staging area.

## Reference architecture

- [Best Practices Git](https://github.com/pskeffington/Best-Practices-Git): research-to-release lifecycle and audit gates.
- [Paul's Notes — public research coding guides](https://github.com/pskeffington/Dartmouth.HSE.Public/tree/main/06_RESOURCES): independent tutorials, visualization interpretation and scientific coding references.
- [Literature matrix](references/LITERATURE_MATRIX.csv): authoritative external methodological and tool documentation, with implementation mapping.

**Scope:** reusable template and pedagogical executable examples; not a claim of independent external validation. This template's implementation is original and does not import private datasets or protected teaching materials.
