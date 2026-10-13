# Research Template — Reproducible Research Starter

**Author: Paul Skeffington · Prepared with OpenAI**

A reusable, independently written starter repository for data science, reproducible research, scientific figures, baseline machine learning, and auditable delivery. Biomedical examples are optional applications, not a fixed study design. Everything in the demonstration is **synthetic**. It does not represent patient records, clinical evidence, regulatory qualification, or production-grade diagnostic software.

## Start a new study in five minutes

Read the [first-project walkthrough](docs/QUICKSTART.md) to install the tool, run a synthetic demonstration, and generate a study-neutral workspace with no clinical or private data.

~~~bash
python -m pip install -e '.[all]'
research-template demo --out artifacts/demo --plots --ml
research-template init-study --out artifacts/studies/my-study \
  --title "My Research Question" --objective descriptive \
  --analysis-unit "one observation per sample"
research-template check-study --root artifacts/studies/my-study
~~~

The initializer produces a blank protocol, variable dictionary, source register, and explicitly blocked release state. It refuses to overwrite an existing directory; the structural checker cannot authorize scientific conclusions or publication.
## R/tidyverse coding standard — optional R workflow

The R research workflow follows the [whole-repository coding contract](docs/CODING_CONVENTIONS.md), the [R style contract](R/STYLE_GUIDE.md), and the [complete R function sheet](R/README.md). It preserves original source names, uses snake_case analysis fields, explicit native `|>` with `dplyr` and `tidyr`, audited join cardinality, clear missing-value denominators, and layered `ggplot2` grammar.

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

To create an independent repository from this starter, the repository owner must first enable the GitHub **Template repository** setting. Once enabled, use **Use this template → Create a new repository**. Until then, clone it normally. Run the new init-study command to create blank study documents, update the package settings for an independent project if needed, and record authorization before reading real data. Do not treat the shared default branch as a staging area.

## Reference architecture

- [Best Practices Git](https://github.com/pskeffington/Best-Practices-Git): research-to-release lifecycle and audit gates.
- [Research literature references](references/LITERATURE_MATRIX.csv): external methods, visualization standards, and reproducibility sources.
- [Literature matrix](references/LITERATURE_MATRIX.csv): authoritative external methodological and tool documentation, with implementation mapping.

**Scope:** reusable template and pedagogical executable examples; not a claim of independent external validation. This template's implementation is original and does not import private datasets or protected teaching materials.


## Manuscript and professional visualization outputs

Use the [R manuscript delivery guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) and [R function atlas](R/README.md) for condition-ordered annotated ComplexHeatmap figures, confidence-interval forest plots, statistically gated volcano displays, separate Plotly exploratory widgets, and static manuscript PDF/PNG exports. Modules are sourced on demand; public release remains a separate scientific and privacy-review gate.


### Publication and journal delivery

This template is **not tied to any dataset, gene panel, cohort, disease, or journal**. Start with your own question, permitted data, codebook, and research protocol. Configure categorical levels, IDs, statistical units, transforms, effect scales, and source licenses for your specific study.

- [Manuscript and figure delivery](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) documents generic PDF/PNG exports, metadata, typography, visual review, supplementary diagnostics, and optional interactive graphics.
- [Journal figure requirements](references/JOURNAL_FIGURE_REQUIREMENTS_MATRIX_2026-10-12.csv) and [reporting frameworks](references/JOURNAL_REPORTING_FRAMEWORKS_2026-10-12.csv) are **dated reference matrices**, not preset requirements or acceptance guarantees. Verify your own target journal's current instructions.
- [R figure modules](R/README.md) cover ggplot2, condition-ordered annotated ComplexHeatmap, forest and volcano plots, and Plotly widgets. These are reusable functions with no required clinical study.
- [Function-call sheet](docs/FUNCTION_CALL_SHEET.md) contains working Python and R calls and preconditions.
- [Research release gates](docs/RELEASE_GATES.md) separate code quality, scientific validity, data rights, and approval to share outputs.

### Use this repository as your own research project

1. Choose **Use this template** on GitHub (once the repository owner enables the *Template repository* setting), or clone the repository.
2. Run the synthetic Python and R examples and baseline tests before substituting your own inputs.
3. Record your study's analysis unit, data dictionary, authorized sources, inclusion/exclusion rules, versioned methods, and assumptions in the project documents.
4. Keep identifiable or licensed data outside a public fork; place outputs in the ignored `artifacts/` directory, and configure explicit validation tests for **your dataset**.
5. Decide whether exploratory plots or hypothesis tests are warranted; report missingness, effect units and uncertainty explicitly. Run human review before any external distribution.

Generic functions are intended to be extended, not to enforce another researcher's study design.

