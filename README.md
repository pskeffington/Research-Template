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


## Manuscript and professional visualization outputs

Use the [R manuscript delivery guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md) and [R function atlas](R/README.md) for condition-ordered annotated ComplexHeatmap figures, confidence-interval forest plots, statistically gated volcano displays, separate Plotly exploratory widgets, and static manuscript PDF/PNG exports. Modules are sourced on demand; public release remains a separate scientific and privacy-review gate.


### Research-aligned PAM50 heatmap delivery

The [manuscript visualization guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md#tcga-brca-pam50-frozen-research-heatmaps-aligned-adapter) includes a reusable R adapter for the frozen TCGA-BRCA discovery signature: **60 genes × 4 subtype paired effects** and **60 genes × 6 planned effect contrasts**. It validates exact frozen gene IDs and ranks, 15 genes per anchor, complete first-minus-second contrast directions and scientific interpretation boundaries. The code never imports protected research inputs unless explicitly called from an authorized private checkout; CI uses synthetic data only. See `R/research_pam50_heatmaps.R` and `R/tests/test_pam50_heatmap_alignment.R`.


**Manuscript preflight:** The research-aligned PAM50 adapter now has a separate hash-pinned full-source loader (`R/research_pam50_sources.R`) and automated PDF geometry check (`scripts/audit_pam50_layout.py`). Both must pass before source-specific review of private R11 research figures. The template does not embed frozen source hashes or research data; the operator must supply independently approved ST06/ST07/ST09 hashes. See [manuscript visualization delivery](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md).

The optional PAM50 **full-range color-scale diagnostic** (`R/research_pam50_scale_diagnostic.R`) explains visually pale/near-zero modeled effects without altering either main heatmap. Its supplementary histogram distinguishes 240 subtype effects from 360 planned contrast values, preserves the same signed scale, and explicitly labels counts as correlated model-output cells rather than patient observations. See the [manuscript guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md).


**Private PAM50 manuscript handoff:** Following frozen ST06/ST07/ST09 source verification and two-panel PDF geometry acceptance, `scripts/build_pam50_review_packet.py` generates a protected, **unsigned** reviewer worksheet and audit JSON in the private output directory. It checks figure/caption provenance and returns `REVIEW_REQUIRED_NOT_APPROVED`; it never signs off science, authorizes public release or merges repository changes. See the [manuscript visualization release guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md).

**Unsigned review governance:** For private manuscript handoff, `scripts/pam50_review_governance.py` adds five revision-linked human decision fields and explicit journal-policy metadata preflight after the verified packet. All decisions default to pending; structural decision validation never grants merge or distribution authorization. See [human review and journal preflight](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md#revision-aware-human-decisions-and-journal-policy-preflight).

### Journal submission and reporting literature matrices (12 October 2026)

The public [journal figure requirements matrix](references/JOURNAL_FIGURE_REQUIREMENTS_MATRIX_2026-10-12.csv) compares nine relevant journals/publisher policies with sourced figure formats, raster resolution, column sizing, legends, reproducibility obligations and compatibility of the existing 9 × 13-in PAM50 heatmap masters. The separate [reporting framework matrix](references/JOURNAL_REPORTING_FRAMEWORKS_2026-10-12.csv) distinguishes STROBE, STREGA, REMARK and TRIPOD+AI by their **actual study design**; their inclusion is not a declaration that all apply. Sources and October 12, 2026 access dates are preserved. BMC Cancer is flagged publisher-general only and requires journal-specific confirmation, as do the finer AACR Cancer Research production limits. These matrices are planning references; new journal-specific derivatives and human permission gates remain required.

**Physical manuscript QA:** In addition to the source/geometry/packet checks, `scripts/audit_manuscript_physical.py` independently opens the two PAM50 PDF/PNG heatmap pairs and supplementary PDF/PNG, checks embedded PDF font data and vector content, measures actual PNG resolution against page inches, and reports detected journal-policy incompatibilities without changing figures. [See the manuscript delivery guide](docs/MANUSCRIPT_VISUALIZATION_DELIVERY.md#independent-physical-pdfpng-export-verification-12-october-2026). Human approval and publication remain separate.

**Journal proof lane:** `scripts/build_journal_proofs.py` supports a read-only figure-size/font feasibility inventory when no target journal has been selected, and explicit proof-only TIFF LZW/EPS derivatives for source-verified journal profiles after human selection. Proportional shrinking below the 8-pt engineering threshold is rejected in favor of an R layout redesign. No derivative is a production-approved or public-release artifact.

**Journal comparison:** `scripts/compare_journal_requirements.py` now compares all dated policy-matrix entries to independently measured font sizes/dimensions for the three master PDFs, flags likely R relayout needs, and keeps publisher-only policies and article-scope mismatches on hold. It is read-only and deliberately selects no publication or exported figure; see the manuscript delivery guide.

**R journal layout planning:** `R/research_pam50_journal_layouts.R` defines read-only two-page, 30-gene planning scenarios for PLOS ONE, PLOS Biology, Nature Communications and Bioinformatics, retaining each 15-gene anchor block and the original shared effect scale. Prospective 9-pt labels and an 8.5-pt legend are layout constraints, not publisher acceptance. The private-only `PAM50_JOURNAL_R_LAYOUT_PLANS.json` records the unsigned plan without emitting modified figures.

**Synthetic publication-size figure QA:** `R/research_pam50_journal_render.R` generates four J03-style 30-gene synthetic ComplexHeatmap PDF/PNG pages for automated typography and footer-clearance inspection. `scripts/audit_pam50_journal_proofs.py` independently validates 30 ordered gene labels per page, embedded fonts, vector cell content, effective DPI, explicit signed legends and SHA-256 provenance. No protected data or public release is involved.

**Protected journal derivative authorization:** `scripts/prepare_private_journal_gate.py` now produces a signed-off-*pending* private request and a SHA-pinned, deliberately blocked execution gate. The new validator cross-checks original figure/provenance audits, nine journal policies, four R page plans, and immutable master files. It cannot render protected-data derivatives or infer scientific/distribution approval from visually reviewed PDFs. See the manuscript delivery guide.
